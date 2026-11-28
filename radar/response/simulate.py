"""T35 — Simulation de candidatures spontanées et de réponses, sur les entreprises RÉELLES (D6).

Les entreprises, leurs scores (T30) et leurs positions sont réels ; seuls les étudiants et les
réponses sont simulés, selon la règle documentée dans `params.yaml` (hypothèses de l'équipe).

Sortie : data/processed/candidatures_simulees.parquet (contrat « candidatures_simulees »).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from radar.config import FILES
from radar.schemas import check_columns

PARAMS_FILE = Path(__file__).with_name("params.yaml")
DOMAIN = "data"

# Variables du modèle, dans l'ordre des coefficients de params.yaml (hors constante).
FEATURES = [
    "c_intensite",
    "c_embauche",
    "log10_effectif",
    "distance_10km",
    "alternance",
    "a_offre_domaine",
]


def load_params(path: Path = PARAMS_FILE) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def candidate_pool(scores: pd.DataFrame, ent: pd.DataFrame) -> pd.DataFrame:
    """Établissements susceptibles de recevoir une candidature (domaine data, géolocalisés)."""
    s = scores[(scores["domaine"] == DOMAIN) & ~scores["volume_suspect"].fillna(False)]
    pool = s.merge(ent[["siret", "lat", "lon"]], on="siret").dropna(subset=["lat", "lon"])
    # D48 : le modèle simulé garde les rangs centiles (params.yaml est calibré dessus)
    for c in ("intensite", "embauche"):
        if f"rang_{c}" in pool:
            pool[f"c_{c}"] = pool[f"rang_{c}"]
    pool = pool.assign(
        log10_effectif=np.log10(pool["effectif_estime"].clip(lower=1).fillna(10)),
        a_offre_domaine=(pool["n_offres_domaine_siren"] > 0).astype(float),
    )
    return pool.reset_index(drop=True)


def true_logit(df: pd.DataFrame, coefs: dict) -> np.ndarray:
    lin = np.full(len(df), coefs["constante"], dtype=float)
    for f in FEATURES:
        lin += coefs[f] * df[f].to_numpy(float)
    return lin


def simulate(pool: pd.DataFrame, params: dict) -> pd.DataFrame:
    rng = np.random.default_rng(params["graine"])
    villes = pd.DataFrame(params["villes"])
    w = villes["poids"] / villes["poids"].sum()
    # Effet aléatoire propre à chaque entreprise (même valeur pour tous ses établissements)
    sirens = pool["siren"].unique()
    u = pd.Series(rng.normal(0, params["sigma_entreprise"], len(sirens)), index=sirens)

    lat, lon = pool["lat"].to_numpy(), pool["lon"].to_numpy()
    sel = np.exp(params["selection_force"] * pool["c_intensite"].to_numpy(float))
    rows = []
    for i in range(params["n_etudiants"]):
        v = villes.iloc[rng.choice(len(villes), p=w)]
        # domicile : autour du centre-ville (± ~5 km)
        hlat, hlon = v["lat"] + rng.normal(0, 0.04), v["lon"] + rng.normal(0, 0.06)
        d = _haversine_km(hlat, hlon, lat, lon)
        near = np.flatnonzero(d <= params["rayon_km"])
        k = min(params["candidatures_par_etudiant"], len(near))
        if k == 0:
            continue
        p = sel[near] / sel[near].sum()
        chosen = rng.choice(near, size=k, replace=False, p=p)
        contrat = "alternance" if rng.random() < params["part_alternance"] else "stage"
        for j in chosen:
            rows.append((f"E{i:05d}", v["nom"], contrat, j, d[j]))

    c = pd.DataFrame(rows, columns=["profil_id", "ville", "contrat_vise", "_j", "distance_km"])
    c = pd.concat([c, pool.loc[c["_j"]].reset_index(drop=True)], axis=1).drop(columns="_j")
    c["domaine"] = DOMAIN
    c["distance_10km"] = c["distance_km"] / 10.0
    c["alternance"] = (c["contrat_vise"] == "alternance").astype(float)
    c["u_entreprise"] = c["siren"].map(u).to_numpy()
    lin = true_logit(c, params["coefficients"]) + c["u_entreprise"].to_numpy()
    c["p_vraie"] = 1 / (1 + np.exp(-lin))
    c["repondu"] = rng.random(len(c)) < c["p_vraie"]
    c["donnees_simulees"] = True  # D6 : toujours signaler que les réponses sont simulées

    keep = ["siret", "siren", "profil_id", "ville", "domaine", "contrat_vise", "distance_km",
            *FEATURES, "u_entreprise", "p_vraie", "repondu", "donnees_simulees"]  # fmt: skip
    out = c[keep]
    check_columns(out, "candidatures_simulees")
    return out


def run(params_path: Path = PARAMS_FILE) -> pd.DataFrame:
    params = load_params(params_path)
    scores = pd.read_parquet(FILES["scores"])
    ent = pd.read_parquet(FILES["entreprises"], columns=["siret", "lat", "lon"])
    cand = simulate(candidate_pool(scores, ent), params)
    cand.to_parquet(FILES["candidatures_simulees"], index=False)
    return cand
