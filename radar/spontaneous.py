"""Couche 2 « Candidature spontanée » (T40, D8, D13).

Entreprises proches de l'étudiant **sans offre correspondante** (domaine × contrat visé),
classées par score. Une entreprise qui a déjà une offre correspondante est dans la couche bleue.

    df = load_nearby(lat, lon, radius_km=20, domaine="data")      # DuckDB, rapide
    out = rank_spontaneous(df, lat, lon, radius_km=20, contrat="stage")

Score (D13, v0) : moyenne géométrique de `c_intensite` et `c_embauche` (les curseurs de poids
arrivent avec T42). Fonctionne avec le `scores.parquet` réel (colonnes `*_siren`,
`volume_suspect`) comme avec les données factices (comptes au niveau du SIRET).
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from radar.config import FILES

EARTH_RADIUS_KM = 6371.0
# Colonnes de entreprises.parquet affichées dans l'app (celles qui manquent sont ignorées).
ENTREPRISE_COLS = (
    "nom",
    "nom_etablissement",
    "commune",
    "naf_libelle",
    "tranche_effectif",
    "lat",
    "lon",
)
ANNUAIRE_URL = "https://annuaire-entreprises.data.gouv.fr/etablissement/{siret}"


def haversine_km(lat: float, lon: float, lats, lons) -> np.ndarray:
    """Distance à vol d'oiseau (km) entre un point et des tableaux de points."""
    lat1, lon1 = np.radians(lat), np.radians(lon)
    lat2, lon2 = np.radians(np.asarray(lats, float)), np.radians(np.asarray(lons, float))
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def bbox(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    """Rectangle (lat_min, lat_max, lon_min, lon_max) qui contient le cercle."""
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(np.cos(np.radians(lat)), 0.01))
    return lat - dlat, lat + dlat, lon - dlon, lon + dlon


def load_nearby(
    lat: float,
    lon: float,
    radius_km: float,
    domaine: str,
    entreprises_path: Path = FILES["entreprises"],
    scores_path: Path = FILES["scores"],
) -> pd.DataFrame:
    """Scores du domaine + infos entreprise, pour les établissements dans le rectangle du rayon.

    DuckDB ne lit que les lignes utiles : pas besoin de charger la France entière en mémoire.
    """
    con = duckdb.connect()
    ent_cols = {
        r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{entreprises_path}'").fetchall()
    }
    score_cols = {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{scores_path}'").fetchall()}
    wanted = [c for c in ENTREPRISE_COLS if c in ent_cols and c not in score_cols]
    select_e = ", ".join(f'e."{c}"' for c in wanted)
    lat_min, lat_max, lon_min, lon_max = bbox(lat, lon, radius_km)
    query = f"""
        SELECT s.*, {select_e}
        FROM '{scores_path}' s
        JOIN '{entreprises_path}' e USING (siret)
        WHERE s.domaine = ?
          AND e.lat BETWEEN ? AND ? AND e.lon BETWEEN ? AND ?
    """
    return con.execute(query, [domaine, lat_min, lat_max, lon_min, lon_max]).df()


def matching_offers(df: pd.DataFrame, contrat: str) -> pd.Series:
    """Nombre d'offres du domaine qui correspondent au contrat visé ("tous" = tout contrat).

    Au niveau de l'entreprise (SIREN) quand le score réel le fournit : si le siège a publié un
    stage data, les autres établissements ne sont pas « sans offre » pour autant (D8, D13).
    """
    suffix = "_siren" if "n_offres_domaine_siren" in df.columns else ""
    total = df[f"n_offres_domaine{suffix}"]
    stage = df[f"n_stage_domaine{suffix}"]
    alt = df[f"n_alternance_domaine{suffix}"]
    return {
        "stage": stage,
        "alternance": alt,
        "emploi": total - stage - alt,
    }.get(contrat, total)


def spontaneous_score(df: pd.DataFrame) -> pd.Series:
    """D13 : moyenne géométrique de l'intensité dans le domaine et du besoin attendu."""
    return np.sqrt(df["c_intensite"].clip(0, 1) * df["c_embauche"].clip(0, 1))


def rank_spontaneous(
    df: pd.DataFrame, lat: float, lon: float, radius_km: float, contrat: str = "tous"
) -> pd.DataFrame:
    """Entreprises du rayon sans offre correspondante, triées par score décroissant.

    Ajoute `distance_km`, `score`, `n_offres_correspondantes` (= 0 par construction) et
    `url_annuaire`. Écarte les `volume_suspect` (intermédiaires non repérés, D13).
    """
    if df.empty:
        return df.assign(distance_km=[], score=[], url_annuaire=[])
    out = df.dropna(subset=["lat", "lon"]).copy()
    out["distance_km"] = haversine_km(lat, lon, out["lat"], out["lon"])
    out = out[out["distance_km"] <= radius_km]
    if "volume_suspect" in out.columns:
        out = out[~out["volume_suspect"].fillna(False).astype(bool)]
    out = out[matching_offers(out, contrat.lower()) == 0]
    out["score"] = spontaneous_score(out)
    out["url_annuaire"] = out["siret"].map(lambda s: ANNUAIRE_URL.format(siret=s))
    return out.sort_values(["score", "distance_km"], ascending=[False, True]).reset_index(drop=True)
