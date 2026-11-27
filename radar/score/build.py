"""Construction de data/processed/scores.parquet (T30) — contrat « scores » (une ligne par
(siret, domaine), composantes c_* dans [0, 1]).

Entrées : entreprises.parquet (T20), offres.parquet rapprochées (T13 + T21),
data/raw/offres_raw/adzuna_couverture.json (couverture de la collecte par région).

Composantes (v0, D13) :
- c_intensite : rang centile de l'intensité a posteriori (offres du domaine / 100 salariés) ;
- c_embauche  : La Bonne Boîte d'abord (`lbb_potentiel`), puis le proxy « besoin attendu »
                (intensité × effectif local) pour les autres → `c_embauche_source` (T28, D27) ;
- c_dynamisme : 0,5 (neutre) tant que les finances ne sont pas chargées (T22) →
                `c_dynamisme_disponible`.
Les établissements d'agences d'intérim / de placement (NAF 78.*) ne sont pas notés.
`volume_suspect` signale les entreprises avec plus d'offres du domaine que la moitié de leur
effectif (intermédiaire non repéré ou entité juridique d'un groupe) : à écarter dans l'app.
"""

from __future__ import annotations

import json
import logging

import numpy as np
import pandas as pd

from radar.collect.lbb import OUT_FILE as LBB_FILE
from radar.collect.lbb import best_by_siret
from radar.config import FILES, PATHS
from radar.geo import region_of
from radar.schemas import check_columns
from radar.score.covariates import CovariateModel
from radar.score.embauche import embauche_component
from radar.score.intensity import fit_priors, posterior

log = logging.getLogger(__name__)

COVERAGE_FILE = PATHS.raw / "offres_raw" / "adzuna_couverture.json"
SCORED_DOMAINS = ("data",)  # la collecte Adzuna ne porte que sur « data » (voir D13)
EXCLUDED_NAF_PREFIX = ("78.",)


def load_coverage(path=COVERAGE_FILE) -> dict[str, float]:
    """Région → part des offres collectées (0 si total inconnu ou région non collectée)."""
    if not path.exists():
        log.warning("%s absent : couverture supposée nulle partout", path)
        return {}
    regions = json.loads(path.read_text())["regions"]
    return {
        r: (v["collectees"] / v["total"]) if v.get("total") else 0.0 for r, v in regions.items()
    }


def pct_rank(s: pd.Series) -> pd.Series:
    return s.rank(pct=True, method="average")


def _dedupe_postings(o: pd.DataFrame, key: str) -> pd.DataFrame:
    """Une offre par (entreprise ou établissement, titre normalisé) : une même annonce publiée
    dans plusieurs villes ou republiée ne compte qu'une fois (9,6 % de doublons, D33 :
    sinon les comptes ne sont pas des événements indépendants)."""
    if o.empty or "titre" not in o.columns:  # source sans titre : pas de dédoublonnage
        return o
    title = (
        o["titre"].fillna("").str.lower()
        .str.replace(r"\(?\b[hf]\s*/\s*[hf]\b\)?", " ", regex=True)
        .str.replace(r"[^a-z0-9àâçéèêëîïôûùüÿœ]+", " ", regex=True)
        .str.strip()
    )  # fmt: skip
    return o.assign(_t=title).drop_duplicates([key, "_t"]).drop(columns="_t")


def _company_table(ent: pd.DataFrame, offres: pd.DataFrame, domain: str, cov: dict) -> pd.DataFrame:
    """Une ligne par SIREN : k (offres du domaine), E (exposition), section NAF, effectif."""
    e = ent.copy()
    e["couv"] = e["departement"].map(region_of).map(cov).fillna(0.0)
    e["eff"] = e["effectif_estime"].fillna(0.0)
    main = e.sort_values("eff", ascending=False).drop_duplicates("siren")
    comp = (
        e.assign(eff_couv=e["eff"] * e["couv"])
        .groupby("siren")
        .agg(effectif_entreprise=("eff", "sum"), eff_couv=("eff_couv", "sum"))
        .join(main.set_index("siren")[["naf_section", "naf_division"]])
    )
    comp["E"] = comp["eff_couv"] / 100.0
    comp["couverture"] = (comp["eff_couv"] / comp["effectif_entreprise"]).fillna(0.0)

    o = offres[(offres["domaine"] == domain) & ~offres["intermediaire"].fillna(False)]
    o = _dedupe_postings(o.dropna(subset=["siren_match"]), "siren_match")
    by_siren = o.assign(stage=o["contrat"].eq("stage"), alt=o["contrat"].eq("alternance")).groupby(
        "siren_match"
    )
    comp["k"] = by_siren.size().reindex(comp.index).fillna(0).astype(int)
    comp["n_stage_domaine_siren"] = (
        by_siren["stage"].sum().reindex(comp.index).fillna(0).astype(int)
    )
    comp["n_alternance_domaine_siren"] = (
        by_siren["alt"].sum().reindex(comp.index).fillna(0).astype(int)
    )
    return comp.reset_index()


def _siret_counts(offres: pd.DataFrame, domain: str) -> pd.DataFrame:
    o = offres[~offres["intermediaire"].fillna(False)].dropna(subset=["siret_match"])
    n_tot = o.groupby("siret_match").size().rename("n_offres")
    d = _dedupe_postings(o[o["domaine"] == domain], "siret_match")
    by = d.assign(stage=d["contrat"].eq("stage"), alt=d["contrat"].eq("alternance")).groupby(
        "siret_match"
    )
    out = pd.concat(
        [
            n_tot,
            by.size().rename("n_offres_domaine"),
            by["stage"].sum().rename("n_stage_domaine"),
            by["alt"].sum().rename("n_alternance_domaine"),
        ],
        axis=1,
    )
    out.index.name = "siret"
    return out.fillna(0).astype(int).reset_index()


def _intensity(
    comp: pd.DataFrame, ent: pd.DataFrame, features: pd.DataFrame | None
) -> pd.DataFrame:
    """Intensité a posteriori par SIREN : v1 (covariables, T69, D33) si les caractéristiques
    sont disponibles, sinon v0 (a priori par secteur NAF seulement, D13)."""
    if features is not None:
        try:
            f = comp.set_index("siren").join(
                features.set_index("siren").drop(
                    columns=["naf_section", "naf_division", "effectif_entreprise"],
                    errors="ignore",
                )
            )
            post = CovariateModel().fit(f).posterior(f)
            out = comp.set_index("siren").join(post).reset_index()
            out["score_version"] = "v1_covariables"
            return out
        except Exception as e:  # données incomplètes : on garde un score, celui de D13
            log.warning("Score v1 impossible (%s) : repli sur v0 (D13)", e)
    out = posterior(comp, fit_priors(comp))
    out["score_version"] = "v0_secteur"
    return out


def build_scores(
    ent: pd.DataFrame,
    offres: pd.DataFrame,
    cov: dict[str, float],
    lbb: pd.DataFrame | None = None,
    features: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """`lbb` : établissements La Bonne Boîte (data/raw/lbb.parquet, T28), ou None → proxy seul.
    `features` : caractéristiques des entreprises (T69), ou None → score v0 (D13)."""
    ent = ent[~ent["naf"].fillna("").str.startswith(EXCLUDED_NAF_PREFIX)]
    frames = []
    for domain in SCORED_DOMAINS:
        comp = _company_table(ent, offres, domain, cov)
        comp = _intensity(comp, ent, features)
        # Plus d'offres du domaine que la moitié de l'effectif en 60 jours : invraisemblable pour
        # un employeur direct (intermédiaire non repéré, ou offres d'un groupe rattachées à une
        # petite entité juridique — SIRENE ne relie pas les sociétés d'un même groupe).
        comp["volume_suspect"] = comp["k"] > 0.5 * comp["effectif_entreprise"]

        s = ent[["siret", "siren", "effectif_estime"]].merge(
            comp.rename(columns={"k": "n_offres_domaine_siren"}), on="siren", how="left"
        )
        s = s.merge(_siret_counts(offres, domain), on="siret", how="left")
        counts = ["n_offres", "n_offres_domaine", "n_stage_domaine", "n_alternance_domaine"]
        s[counts] = s[counts].fillna(0).astype(int)
        s["domaine"] = domain
        s["c_intensite"] = pct_rank(s["intensite_post"])
        # Besoin attendu au niveau de l'ÉTABLISSEMENT (intensité de l'entreprise × effectif local) :
        # au niveau entreprise, chaque bureau de La Poste hériterait de 250 000 salariés.
        s["besoin_attendu"] = s["intensite_post"] * s["effectif_estime"].fillna(0) / 100.0
        # T28 (D27) : La Bonne Boîte devant, proxy pour les autres (radar/score/embauche.py).
        lbb_best = best_by_siret(lbb, domain) if lbb is not None else None
        s = embauche_component(s, lbb_best)
        s["c_dynamisme"] = 0.5
        s["c_dynamisme_disponible"] = False
        frames.append(s)

    out = pd.concat(frames, ignore_index=True)
    floats = out.select_dtypes("float64").columns
    out[floats] = out[floats].astype(np.float32)
    check_columns(out, "scores_reels")
    return out


def run() -> pd.DataFrame:
    ent = pd.read_parquet(FILES["entreprises"])
    offres = pd.read_parquet(FILES["offres"])
    check_columns(offres, "offres_rapprochees")
    lbb = pd.read_parquet(LBB_FILE) if LBB_FILE.exists() else None
    if lbb is None:
        log.warning("%s absent : c_embauche = proxy seul (lancer scripts/collect_lbb.py)", LBB_FILE)
    try:  # T69 : caractéristiques (SIRENE, BODACC capital, densité), en cache dans data/raw/
        from radar.score.features import build_features

        features = build_features(ent[~ent["naf"].fillna("").str.startswith(EXCLUDED_NAF_PREFIX)])
    except Exception as e:  # pas de réseau au premier lancement, etc.
        log.warning("Caractéristiques indisponibles (%s) : score v0 (D13)", e)
        features = None
    out = build_scores(ent, offres, load_coverage(), lbb, features)
    out.to_parquet(FILES["scores"], index=False)
    return out
