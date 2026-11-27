"""Recruteurs potentiels La bonne alternance dans la couche orange (T51).

    df = mark_lba_recruiters(nearby, domaine="data")   # ajoute `recruteur_lba` (bool)

`data/raw/lba_recruteurs.parquet` (T11, T17) liste les entreprises que La bonne alternance juge
susceptibles d'embaucher des alternants **sans offre publiée**, avec leurs codes ROME. Une
entreprise est marquée si l'un de ses codes ROME est un code **non ambigu** du domaine
(`rome` dans `radar/domains.yaml`, pas `rome_partiel`). C'est un signal d'opportunité cachée
pour l'alternance (composante `c_recruteur_lba` du score, `radar/spontaneous.py`).
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from radar.config import PATHS
from radar.domains import load_domains

RECRUITERS_FILE = PATHS.raw / "lba_recruteurs.parquet"


def domain_rome_codes(domaine: str) -> list[str]:
    """Codes ROME non ambigus du domaine ([] si domaine inconnu)."""
    d = load_domains().get(domaine)
    return sorted(d.rome) if d else []


def lba_recruiter_sirets(sirets: list[str], domaine: str, path: Path | None = None) -> set[str]:
    """SIRET (parmi ceux demandés) recruteurs LBA sur au moins un code ROME du domaine."""
    path = path or RECRUITERS_FILE
    codes = domain_rome_codes(domaine)
    if not sirets or not codes or not path.exists():
        return set()
    con = duckdb.connect()
    con.register("wanted", pd.DataFrame({"siret": [str(s) for s in sirets]}))
    rows = con.execute(
        f"""
        SELECT DISTINCT CAST(r.siret AS VARCHAR)
        FROM '{path}' r JOIN wanted w ON CAST(r.siret AS VARCHAR) = w.siret
        WHERE list_has_any(
            list_transform(string_split(coalesce(r.code_rome, ''), ','), lambda x: trim(x)), ?
        )
        """,
        [codes],
    ).fetchall()
    return {r[0] for r in rows}


def mark_lba_recruiters(df: pd.DataFrame, domaine: str, path: Path | None = None) -> pd.DataFrame:
    """Ajoute la colonne booléenne `recruteur_lba`."""
    out = df.copy()
    if out.empty or "siret" not in out:
        return out.assign(recruteur_lba=pd.Series(dtype=bool))
    found = lba_recruiter_sirets(out["siret"].astype(str).tolist(), domaine, path)
    out["recruteur_lba"] = out["siret"].astype(str).isin(found)
    return out
