"""T34 — Validation du score sans vérité terrain (stabilité, sensibilité aux poids, cohérence).

Il n'existe pas de données « cette entreprise a répondu / embauché un stagiaire » : on ne peut
pas mesurer une précision. On vérifie à la place que le classement de la couche orange :
1. est STABLE quand les offres observées varient (bootstrap sur les offres data) ;
2. ne dépend pas d'un réglage précis des POIDS (curseurs) ;
3. est COHÉRENT avec des sources indépendantes de nos offres : La Bonne Boîte (déclarations
   d'embauche) et les recruteurs potentiels de La bonne alternance, comparé à une référence
   naïve (« les plus grosses entreprises d'abord »).

Fonctions pures + `run()` utilisé par `scripts/validate_scores.py`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from radar.collect.lbb import best_by_siret
from radar.recruteurs import domain_rome_codes
from radar.score.build import EXCLUDED_NAF_PREFIX, _company_table
from radar.score.embauche import embauche_component
from radar.score.intensity import fit_priors
from radar.spontaneous import COMPONENTS, DEFAULT_WEIGHTS, rank_spontaneous

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class City:
    name: str
    lat: float
    lon: float


CITIES = [
    City("Rennes", 48.1173, -1.6778),
    City("Paris", 48.8566, 2.3522),
    City("Lyon", 45.7640, 4.8357),
    City("Toulouse", 43.6047, 1.4442),
]
RADIUS_KM = 20
TOP_K = 20
CONTRACTS = ("stage", "alternance")


# --------------------------------------------------------------------------- métriques


def overlap_at_k(a: list, b: list, k: int = TOP_K) -> float:
    """Part des k premiers de `a` qui sont aussi dans les k premiers de `b` (1 = identiques)."""
    a, b = list(a)[:k], list(b)[:k]
    if not a:
        return np.nan
    return len(set(a) & set(b)) / len(a)


def auc(score: pd.Series, label: pd.Series) -> float:
    """Aire sous la courbe ROC (Mann-Whitney) : P(score d'un positif > score d'un négatif).

    0,5 = hasard, 1 = parfait. Les ex aequo comptent pour moitié.
    """
    s = pd.Series(score).astype(float)
    y = pd.Series(label).astype(bool).reindex(s.index)
    ok = s.notna()
    s, y = s[ok], y[ok]
    n1, n0 = int(y.sum()), int((~y).sum())
    if n1 == 0 or n0 == 0:
        return np.nan
    r = s.rank(method="average")
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def roc_points(score: pd.Series, label: pd.Series, n: int = 50) -> list[tuple[float, float]]:
    """Points (taux de faux positifs, taux de vrais positifs) pour tracer la courbe ROC."""
    s = pd.Series(score).astype(float)
    y = pd.Series(label).astype(bool).reindex(s.index)
    ok = s.notna()
    s, y = s[ok], y[ok]
    pts = [(0.0, 0.0)]
    for q in np.linspace(1, 0, n + 1)[1:]:
        t = s.quantile(q)
        pred = s >= t
        pts.append(
            (
                float((pred & ~y).sum() / max((~y).sum(), 1)),
                float((pred & y).sum() / max(y.sum(), 1)),
            )
        )
    return pts


# --------------------------------------------------------------------------- recalcul du score


class ScoreRecomputer:
    """Recalcule `c_intensite` et `c_embauche` (par SIRET) pour d'autres comptes d'offres.

    Reprend exactement la chaîne de `radar/score/build.py` (gamma-Poisson par division NAF,
    D13 ; La Bonne Boîte puis proxy, D27), sans les intervalles crédibles (inutiles ici, lents).
    """

    def __init__(
        self, ent: pd.DataFrame, offres: pd.DataFrame, cov: dict, lbb: pd.DataFrame | None
    ):
        ent = ent[~ent["naf"].fillna("").str.startswith(EXCLUDED_NAF_PREFIX)]
        self.comp = _company_table(ent, offres, "data", cov)  # k observé inclus
        self.etab = ent[["siret", "siren", "effectif_estime"]].reset_index(drop=True)
        self.lbb_best = best_by_siret(lbb, "data") if lbb is not None else None
        o = offres[(offres["domaine"] == "data") & ~offres["intermediaire"].fillna(False)]
        self.usable_offers = o.dropna(subset=["siren_match"])["siren_match"].to_numpy()

    def components(self, k: pd.Series | None = None) -> pd.DataFrame:
        """`k` : offres data par SIREN (None = comptes observés). Une ligne par SIRET."""
        comp = self.comp.copy()
        if k is not None:
            comp["k"] = k.reindex(comp["siren"]).fillna(0).to_numpy()
        priors = fit_priors(comp)
        glob = priors["__global__"]
        a0 = comp["naf_division"].map(lambda g: priors.get(g, glob).alpha).astype(float)
        b0 = comp["naf_division"].map(lambda g: priors.get(g, glob).beta).astype(float)
        comp["intensite_post"] = (a0 + comp["k"]) / (b0 + comp["E"])
        s = self.etab.merge(comp[["siren", "intensite_post"]], on="siren", how="left")
        s["c_intensite"] = s["intensite_post"].rank(pct=True, method="average")
        s["besoin_attendu"] = s["intensite_post"] * s["effectif_estime"].fillna(0) / 100.0
        s = embauche_component(s, self.lbb_best)
        return s[["siret", "intensite_post", "c_intensite", "c_embauche"]].set_index("siret")

    def bootstrap_k(self, rng: np.random.Generator) -> pd.Series:
        """Tirage avec remise des offres data rapprochées → nouveaux comptes par SIREN."""
        draw = rng.choice(self.usable_offers, size=len(self.usable_offers), replace=True)
        return pd.Series(draw).value_counts()


def ranked_sirets(
    nearby: pd.DataFrame, comps: pd.DataFrame, city: City, contrat: str, weights: dict | None = None
) -> list[str]:
    """Classement orange (SIRET dans l'ordre) avec des composantes recalculées."""
    df = nearby.copy()
    df["c_intensite"] = df["siret"].map(comps["c_intensite"])
    df["c_embauche"] = df["siret"].map(comps["c_embauche"])
    out = rank_spontaneous(df, city.lat, city.lon, RADIUS_KM, contrat, weights or DEFAULT_WEIGHTS)
    return out["siret"].tolist()


# --------------------------------------------------------------------------- analyses


def stability(
    rec: ScoreRecomputer, nearby: dict[str, pd.DataFrame], n_boot: int, seed: int = 0
) -> pd.DataFrame:
    """overlap@k entre le classement observé et chaque tirage bootstrap, par ville × contrat."""
    rng = np.random.default_rng(seed)
    base = rec.components()
    ref = {
        (c.name, ct): ranked_sirets(nearby[c.name], base, c, ct) for c in CITIES for ct in CONTRACTS
    }
    rows = []
    for b in range(n_boot):
        comps = rec.components(rec.bootstrap_k(rng))
        for c in CITIES:
            for ct in CONTRACTS:
                r = ranked_sirets(nearby[c.name], comps, c, ct)
                rows.append(
                    {
                        "tirage": b,
                        "ville": c.name,
                        "contrat": ct,
                        "overlap": overlap_at_k(ref[(c.name, ct)], r),
                    }
                )
        log.info("bootstrap %d/%d", b + 1, n_boot)
    return pd.DataFrame(rows)


def weight_sensitivity(
    rec: ScoreRecomputer, nearby: dict[str, pd.DataFrame], n_random: int, seed: int = 0
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(1) poids tirés au hasard (0 à 5) ; (2) un curseur à la fois mis à 0 puis à 5."""
    rng = np.random.default_rng(seed)
    base = rec.components()
    keys = list(COMPONENTS)
    rand_rows, ofat_rows = [], []
    for c in CITIES:
        for ct in CONTRACTS:
            ref = ranked_sirets(nearby[c.name], base, c, ct)
            for i in range(n_random):
                w = {k: int(rng.integers(0, 6)) for k in keys}
                if not any(w.values()):
                    w[keys[0]] = 1
                r = ranked_sirets(nearby[c.name], base, c, ct, w)
                rand_rows.append(
                    {"ville": c.name, "contrat": ct, "essai": i, "overlap": overlap_at_k(ref, r)}
                )
            for k in keys:
                for v in (0, 5):
                    w = dict(DEFAULT_WEIGHTS, **{k: v})
                    if w == DEFAULT_WEIGHTS or not any(w.values()):
                        continue
                    r = ranked_sirets(nearby[c.name], base, c, ct, w)
                    ofat_rows.append(
                        {
                            "ville": c.name,
                            "contrat": ct,
                            "composante": k,
                            "poids": v,
                            "overlap": overlap_at_k(ref, r),
                        }
                    )
    return pd.DataFrame(rand_rows), pd.DataFrame(ofat_rows)


def external_coherence(
    rec: ScoreRecomputer, scores: pd.DataFrame, lba_rec: pd.DataFrame
) -> pd.DataFrame:
    """AUC de nos composantes pour retrouver des établissements signalés par d'autres sources.

    Étiquettes indépendantes de nos offres :
    - `lbb` : établissement listé par La Bonne Boîte sur un métier data (déclarations d'embauche) ;
    - `lba` : recruteur potentiel La bonne alternance sur un code ROME data.
    Comparé à la référence naïve « effectif » (les gros établissements recrutent plus).
    Calculé sur tous les établissements, puis sur ceux SANS offre data (la couche orange).
    """
    base = rec.components()
    data_codes = set(domain_rome_codes("data"))
    codes = lba_rec[["siret", "code_rome"]].dropna()
    lba_sirets = set(
        codes.loc[
            codes["code_rome"].str.split(",").map(lambda codes_: bool(set(codes_) & data_codes)),
            "siret",
        ]
    )
    df = rec.etab.set_index("siret").join(base)
    df = df.join(scores.drop_duplicates("siret").set_index("siret")[["n_offres_domaine_siren"]])
    lbb_sirets = set(rec.lbb_best["siret"]) if rec.lbb_best is not None else set()
    df["lbb"] = df.index.isin(lbb_sirets)
    df["lba"] = df.index.isin(lba_sirets)
    rows = []
    for pop, sub in [
        ("tous", df),
        ("sans offre data", df[df["n_offres_domaine_siren"].fillna(0) == 0]),
    ]:
        for label in ("lbb", "lba"):
            rows.append(
                {
                    "population": pop,
                    "etiquette": label,
                    "n": len(sub),
                    "positifs": int(sub[label].sum()),
                    "auc_intensite": auc(sub["c_intensite"], sub[label]),
                    "auc_effectif": auc(sub["effectif_estime"], sub[label]),
                    "auc_intensite_x_effectif": auc(
                        sub["intensite_post"] * sub["effectif_estime"].fillna(0), sub[label]
                    ),
                }
            )
    return pd.DataFrame(rows), df
