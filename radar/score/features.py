"""T69 — Caractéristiques de la situation des entreprises, pour le score v1 (covariables).

Toutes les sources sont ouvertes et sans clé ; chaque collecte est mise en cache dans data/raw/.

- `capital_changes()` : annonces BODACC de **modification du capital** des 2 dernières années
  (proxy ouvert des levées de fonds / recapitalisations), par SIREN ;
- `sirene_extra()` : date de création, catégorie juridique, ESS, société à mission ;
- `data_density()` : nombre d'établissements de secteurs data (NAF 62, 63.1, 72.19, 73.20, 58.2)
  à moins de `radius_km` (effet d'agglomération : technopôles) ;
- `build_features()` : une ligne par SIREN, prête pour la régression ; ajoute la note LLM
  secteur × taille de l'établissement principal (`note_llm_<domaine>`, T77) si la grille existe.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

import duckdb
import numpy as np
import pandas as pd
import requests

from radar.collect.bodacc import EXPORT_URL
from radar.collect.sirene import URL_UNITES_LEGALES
from radar.config import PATHS, USER_AGENT
from radar.score.llm_grid import establishment_notes, load_grid

log = logging.getLogger(__name__)

CAPITAL_FILE = PATHS.raw / "bodacc_capital.parquet"
SIRENE_EXTRA_FILE = PATHS.raw / "sirene_ul_extra.parquet"
DATA_NAF_RE = r"^(62\.|63\.1|72\.19|73\.20|58\.2)"
CAPITAL_YEARS = 2


def capital_changes(refresh: bool = False, timeout: int = 900) -> pd.DataFrame:
    """SIREN, date, augmentation explicite : modifications du capital publiées au BODACC."""
    if CAPITAL_FILE.exists() and not refresh:
        return pd.read_parquet(CAPITAL_FILE)
    since = date.today() - timedelta(days=365 * CAPITAL_YEARS)
    params = {
        "select": "registre,dateparution,modificationsgenerales",
        "where": (
            f"familleavis=\"modification\" AND dateparution >= date'{since.isoformat()}' "
            'AND search(modificationsgenerales, "capital")'
        ),
    }
    log.info("Téléchargement des modifications de capital (BODACC, depuis %s)…", since)
    resp = requests.get(
        EXPORT_URL, params=params, timeout=timeout, headers={"User-Agent": USER_AGENT}
    )
    resp.raise_for_status()
    tmp = CAPITAL_FILE.with_suffix(".tmp")
    tmp.write_bytes(resp.content)
    raw = pd.read_parquet(tmp)
    tmp.unlink()

    def siren(reg) -> str | None:
        # « 499 060 473,499060473 » (chaîne) ou liste selon l'export
        vals = list(reg) if reg is not None and not isinstance(reg, str) else str(reg).split(",")
        for v in vals:
            s = str(v or "").replace(" ", "")
            if len(s) == 9 and s.isdigit():
                return s
        return None

    out = pd.DataFrame(
        {
            "siren": raw["registre"].map(siren),
            "date": pd.to_datetime(raw["dateparution"], errors="coerce"),
            "augmentation": raw["modificationsgenerales"]
            .astype(str)
            .str.contains("augmentation", case=False),
        }
    ).dropna(subset=["siren"])
    out.to_parquet(CAPITAL_FILE, index=False)
    log.info("%s annonces de capital, %s SIREN", len(out), out["siren"].nunique())
    return out


def sirene_extra(sirens: list[str], refresh: bool = False) -> pd.DataFrame:
    """Champs de StockUniteLegale non extraits par T20, pour les SIREN du référentiel."""
    if SIRENE_EXTRA_FILE.exists() and not refresh:
        return pd.read_parquet(SIRENE_EXTRA_FILE)
    con = duckdb.connect()
    con.sql("INSTALL httpfs; LOAD httpfs; SET http_timeout = 600000; SET http_retries = 5;")
    con.register("ref", pd.DataFrame({"siren": sorted(set(sirens))}))
    df = con.sql(
        f"""
        SELECT u.siren,
               TRY_CAST(u.dateCreationUniteLegale AS DATE) AS date_creation,
               u.categorieJuridiqueUniteLegale AS categorie_juridique,
               u.economieSocialeSolidaireUniteLegale = 'O' AS ess,
               u.societeMissionUniteLegale = 'O' AS societe_mission
        FROM read_parquet('{URL_UNITES_LEGALES}') u
        JOIN ref USING (siren)
        """
    ).df()
    df.to_parquet(SIRENE_EXTRA_FILE, index=False)
    return df


def data_density(ent: pd.DataFrame, radius_km: float = 3.0) -> pd.Series:
    """Nombre d'établissements de secteurs data à moins de `radius_km` (hors lui-même)."""
    from sklearn.neighbors import BallTree

    pts = ent[["lat", "lon"]].to_numpy(float)
    ok = ~np.isnan(pts).any(axis=1)
    is_data = ent["naf"].fillna("").str.match(DATA_NAF_RE).to_numpy()
    tree = BallTree(np.radians(pts[ok & is_data]), metric="haversine")
    counts = np.zeros(len(ent))
    counts[ok] = tree.query_radius(np.radians(pts[ok]), r=radius_km / 6371.0, count_only=True)
    counts -= is_data & ok  # ne pas se compter soi-même
    return pd.Series(counts, index=ent.index, name="densite_data")


def build_features(ent: pd.DataFrame, today: date | None = None) -> pd.DataFrame:
    """Une ligne par SIREN : covariables de la régression (sans valeur manquante)."""
    today = today or date.today()
    e = ent.copy()
    e["densite_data"] = data_density(e)
    e["eff"] = e["effectif_estime"].fillna(10)
    main = e.sort_values("eff", ascending=False).drop_duplicates("siren").set_index("siren")
    agg = e.groupby("siren").agg(
        n_etab=("siret", "size"),
        effectif_entreprise=("eff", "sum"),
        densite_data=("densite_data", "max"),
    )
    f = agg.join(main[["naf_section", "naf_division", "naf", "categorie"]])
    # T77 : note LLM (secteur × taille) de l'établissement principal, si la grille existe
    grid = load_grid()
    if grid is not None:
        notes = establishment_notes(main.reset_index(), grid).set_index(main.index)
        f = f.join(notes)

    extra = sirene_extra(f.index.tolist()).set_index("siren")
    f = f.join(extra)
    age = (pd.Timestamp(today) - pd.to_datetime(f["date_creation"])).dt.days / 365.25
    f["age_ans"] = age.clip(0, 100).fillna(age.median())

    cap = capital_changes()
    since = pd.Timestamp(today) - pd.Timedelta(days=365 * CAPITAL_YEARS)
    cap = cap[cap["date"] >= since]
    f["n_modif_capital"] = cap.groupby("siren").size().reindex(f.index).fillna(0)
    f["augmentation_capital"] = (
        cap[cap["augmentation"]].groupby("siren").size().reindex(f.index).fillna(0) > 0
    )
    f["ess"] = f["ess"].fillna(False).astype(bool)
    f["societe_mission"] = f["societe_mission"].fillna(False).astype(bool)
    return f.reset_index()
