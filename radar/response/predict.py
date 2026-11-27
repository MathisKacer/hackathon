"""P(réponse) dans l'app (T37, D18) — démonstrateur entraîné sur des réponses SIMULÉES.

    coef = load_coefficients()                       # None si le modèle n'a pas été construit
    df = add_p_reponse(spontaneous, domaine="data", contrat="Stage", coef=coef)

`p_reponse.parquet` donne P(réponse) par (siret, domaine, contrat_vise) à distance NULLE ; on
ajoute le terme de distance au logit : logit(p) = logit(p0) + coef['distance_10km'] × km / 10.
Contrats : stage et alternance seulement ; « Tous » = moyenne des deux ; « Emploi » : rien
(le modèle ne couvre pas l'emploi). Toujours afficher que les réponses sont simulées.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from radar.config import FILES, PATHS

MODEL_FILE = PATHS.processed / "modele_reponse.json"
CONTRATS_MODELE = ("stage", "alternance")


def load_coefficients(path: Path | None = None) -> dict[str, float] | None:
    """Coefficients de la logistique (modele_reponse.json), None s'il n'existe pas."""
    path = path or MODEL_FILE
    if not path.exists():
        return None
    return {k: float(v) for k, v in json.loads(path.read_text())["coefficients"].items()}


def contracts_for(contrat: str) -> list[str]:
    """Contrats du modèle à utiliser pour le contrat visé ([] si non couvert)."""
    c = contrat.lower()
    if c in CONTRATS_MODELE:
        return [c]
    return list(CONTRATS_MODELE) if c == "tous" else []


def load_p_reponse(
    sirets: list[str], domaine: str, contrats: list[str], path: Path | None = None
) -> pd.DataFrame:
    """P(réponse) à distance nulle des SIRET demandés (moyenne si plusieurs contrats)."""
    path = path or FILES["p_reponse"]
    empty = pd.DataFrame({"siret": pd.Series(dtype=str), "p_reponse_0": pd.Series(dtype=float)})
    if not sirets or not contrats or not path.exists():
        return empty
    con = duckdb.connect()
    con.register("wanted", pd.DataFrame({"siret": [str(s) for s in sirets]}))
    marks = ", ".join("?" for _ in contrats)
    df = con.execute(
        f"""
        SELECT CAST(p.siret AS VARCHAR) AS siret, AVG(p.p_reponse) AS p_reponse_0
        FROM '{path}' p JOIN wanted w ON CAST(p.siret AS VARCHAR) = w.siret
        WHERE p.domaine = ? AND p.contrat_vise IN ({marks})
        GROUP BY 1
        """,
        [domaine, *contrats],
    ).df()
    return df if not df.empty else empty


def with_distance(p0, distance_km, coef_distance_10km: float) -> np.ndarray:
    """Ajoute l'effet de la distance au logit de la probabilité à distance nulle."""
    p0 = np.clip(np.asarray(p0, float), 1e-6, 1 - 1e-6)
    logit = np.log(p0 / (1 - p0)) + coef_distance_10km * np.asarray(distance_km, float) / 10
    return 1 / (1 + np.exp(-logit))


def add_p_reponse(
    df: pd.DataFrame,
    domaine: str,
    contrat: str,
    coef: dict[str, float] | None,
    path: Path | None = None,
) -> pd.DataFrame:
    """Ajoute `p_reponse` (ajustée de la distance) ; NaN quand le modèle ne couvre pas le cas."""
    out = df.copy()
    out["p_reponse"] = np.nan
    if out.empty or coef is None:
        return out
    p = load_p_reponse(out["siret"].astype(str).tolist(), domaine, contracts_for(contrat), path)
    if p.empty:
        return out
    p0 = out["siret"].astype(str).map(p.set_index("siret")["p_reponse_0"])
    known = p0.notna()
    out.loc[known, "p_reponse"] = with_distance(
        p0[known], out.loc[known, "distance_km"], coef.get("distance_10km", 0.0)
    )
    return out
