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
from radar.procedures import apply_procedures

EARTH_RADIUS_KM = 6371.0
# Colonnes de entreprises.parquet affichées dans l'app (celles qui manquent sont ignorées).
ENTREPRISE_COLS = (
    "nom",
    "nom_etablissement",
    "commune",
    "naf",
    "naf_section",
    "naf_libelle",
    "tranche_effectif",
    "lat",
    "lon",
    # Situation BODACC (T23, D24) : alerte et pénalité, voir radar/procedures.py
    "procedure_type",
    "procedure_date",
    "procedure_url",
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
    """D13 : moyenne géométrique de l'intensité dans le domaine et du potentiel d'embauche."""
    return np.sqrt(df["c_intensite"].clip(0, 1) * df["c_embauche"].clip(0, 1))


# Composantes du score pondéré (T42) : colonne → (libellé court, explication). Toutes dans [0, 1].
COMPONENTS: dict[str, tuple[str, str]] = {
    "c_intensite": (
        "Intensité dans le domaine",
        "Offres du domaine par salarié, rétrécies vers le secteur (bayésien empirique, D13).",
    ),
    "c_embauche": (
        "Potentiel d'embauche",
        "Établissements signalés par La Bonne Boîte (France Travail) comme susceptibles "
        "d'embaucher sur un métier du domaine : en tête, classés par leur potentiel. "
        "Les autres : estimation à partir des offres du secteur et de l'effectif (T28, D27).",
    ),
    "c_proximite": (
        "Proximité",
        "1 à ton adresse, 0 au bord du rayon.",
    ),
    "c_cachee": (
        "Opportunité cachée",
        "1 si l'entreprise publie des offres du domaine, mais aucune pour ton contrat.",
    ),
    "c_recruteur_lba": (
        "Recruteur d'alternants (LBA)",
        "1 si La bonne alternance signale l'entreprise comme recruteur potentiel d'alternants "
        "sur un métier du domaine, sans offre publiée (T51). Compte en alternance et « Tous ».",
    ),
    "c_dynamisme": (
        "Dynamisme",
        "Croissance de l'entreprise (T22) ; neutre (0,5) tant que les finances manquent.",
    ),
}
# Poids par défaut (curseurs 0 à 5) : proches du classement D13, avec un peu de proximité.
DEFAULT_WEIGHTS: dict[str, int] = {
    "c_intensite": 3,
    "c_embauche": 3,
    "c_proximite": 1,
    "c_cachee": 1,
    "c_recruteur_lba": 2,
    "c_dynamisme": 0,
}
# Composantes qui n'ont de sens que pour certains contrats visés : ailleurs, leur poids est
# ignoré (sinon elles valent 0 partout et font baisser tous les scores sans rien classer).
COMPONENT_CONTRACTS: dict[str, tuple[str, ...]] = {
    "c_cachee": ("stage", "alternance", "emploi"),
    "c_recruteur_lba": ("alternance", "tous"),
}


LBB_SOURCE = "la_bonne_boite"  # valeur de `c_embauche_source` (radar/score/embauche.py, T28)


def signaled_by_lbb(df: pd.DataFrame) -> pd.Series:
    """True pour les établissements dont `c_embauche` vient de La Bonne Boîte (T29, D27).

    Faux partout si la colonne manque (scores d'avant T28, données factices).
    """
    if "c_embauche_source" not in df.columns:
        return pd.Series(False, index=df.index)
    return df["c_embauche_source"].eq(LBB_SOURCE).fillna(False)


def applicable_weights(weights: dict[str, float], contrat: str) -> dict[str, float]:
    """Poids sans les composantes hors sujet pour le contrat visé."""
    c = contrat.lower()
    return {k: v for k, v in weights.items() if c in COMPONENT_CONTRACTS.get(k, (c,))}


def add_user_components(df: pd.DataFrame, radius_km: float, contrat: str) -> pd.DataFrame:
    """Composantes qui dépendent de l'étudiant : proximité, opportunité cachée, recruteur LBA."""
    out = df.copy()
    out["c_proximite"] = (1 - out["distance_km"] / max(radius_km, 1e-9)).clip(0, 1)
    suffix = "_siren" if "n_offres_domaine_siren" in out.columns else ""
    has_domain_offers = out[f"n_offres_domaine{suffix}"].fillna(0) > 0
    no_matching = matching_offers(out, contrat.lower()).fillna(0) == 0
    out["c_cachee"] = (has_domain_offers & no_matching).astype(float)
    if "c_dynamisme" not in out.columns:
        out["c_dynamisme"] = 0.5
    # T51 : recruteur LBA sur un métier du domaine (colonne posée par radar.recruteurs).
    lba = out["recruteur_lba"] if "recruteur_lba" in out.columns else False
    in_scope = contrat.lower() in COMPONENT_CONTRACTS["c_recruteur_lba"]
    out["c_recruteur_lba"] = (pd.Series(lba, index=out.index).fillna(False) & in_scope).astype(
        float
    )
    return out


def weighted_score(df: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    """score = Σ wⱼ·cⱼ / Σ wⱼ (dans [0, 1]) + une colonne `apport_<composante>` par composante.

    L'apport est la part du score due à la composante (la somme des apports = le score) ;
    NaN pour une composante de poids nul. Tous les poids à 0 : repli sur le score D13.
    """
    out = df.copy()
    w = {k: float(v) for k, v in weights.items() if k in COMPONENTS and float(v) > 0}
    total = sum(w.values())
    for k in COMPONENTS:
        # Composante sans poids (ou hors sujet pour le contrat) : apport NaN, masqué dans l'app.
        out[f"apport_{k}"] = out[k].clip(0, 1).fillna(0) * w[k] / total if k in w else np.nan
    out["score"] = (
        out[[f"apport_{k}" for k in COMPONENTS]].sum(axis=1) if total else spontaneous_score(out)
    )
    return out


def rank_spontaneous(
    df: pd.DataFrame,
    lat: float,
    lon: float,
    radius_km: float,
    contrat: str = "tous",
    weights: dict[str, float] | None = None,
    show_liquidation: bool = False,
) -> pd.DataFrame:
    """Entreprises du rayon sans offre correspondante, triées par score décroissant.

    Ajoute `distance_km`, `score`, `url_annuaire`, les composantes `c_proximite`, `c_cachee`
    et, avec `weights` (T42), les colonnes `apport_<composante>`. Sans `weights` : score D13.
    Écarte les `volume_suspect` (intermédiaires non repérés, D13).
    Procédures collectives (T23, D24) : score multiplié par `coef_procedure` selon la situation
    et le contrat, colonne `alerte` ; entreprises en liquidation masquées sauf `show_liquidation`.
    """
    if df.empty:
        return df.assign(distance_km=[], score=[], url_annuaire=[])
    out = df.dropna(subset=["lat", "lon"]).copy()
    out["distance_km"] = haversine_km(lat, lon, out["lat"], out["lon"])
    out = out[out["distance_km"] <= radius_km]
    if "volume_suspect" in out.columns:
        out = out[~out["volume_suspect"].fillna(False).astype(bool)]
    out = add_user_components(out, radius_km, contrat)
    out = out[matching_offers(out, contrat.lower()) == 0]
    if weights is None:
        out["score"] = spontaneous_score(out)
    else:
        out = weighted_score(out, applicable_weights(weights, contrat))
    out = apply_procedures(out, contrat, show_liquidation)
    out["url_annuaire"] = out["siret"].map(lambda s: ANNUAIRE_URL.format(siret=s))
    return out.sort_values(["score", "distance_km"], ascending=[False, True]).reset_index(drop=True)
