"""T21 — Complète data/processed/offres.parquet avec le rapprochement nom + position → SIRET.

Conformément à D10 : T13 (`scripts/classify_offres.py`, @emma) écrit `offres.parquet`
(domaine, contrat, SIRET fourni par la source). Ici, on relit ce fichier et on ne complète que
les lignes `match_methode == "a_rapprocher"`. Les autres (`siret_source`, `siret_ecole_exclu`)
ne sont pas modifiées, sauf l'ajout des colonnes communes (`siren_match`, `match_confiance`…).

Pipeline : collecteurs → classify_offres.py → match_offres.py → score.
"""

from __future__ import annotations

import logging

import pandas as pd

from radar.config import FILES
from radar.process.classify import MATCH_FROM_SOURCE, MATCH_TODO
from radar.process.match_siret import match_offers, match_report
from radar.schemas import check_columns

log = logging.getLogger(__name__)

MATCH_COLUMNS = ["siret_match", "match_score", "match_methode"]


def complete_matches(offres: pd.DataFrame, entreprises: pd.DataFrame) -> pd.DataFrame:
    todo = offres["match_methode"].eq(MATCH_TODO)
    matched = match_offers(offres[todo].drop(columns=MATCH_COLUMNS), entreprises)

    rest = offres[~todo].copy()
    from_source = rest["match_methode"].eq(MATCH_FROM_SOURCE)
    rest["siren_match"] = rest["siret_match"].astype("string").str[:9].where(from_source)
    rest["match_confiance"] = pd.Series("haute", index=rest.index).where(from_source)
    rest["match_distance_km"] = None
    rest["intermediaire"] = False

    out = pd.concat([matched, rest], ignore_index=True)
    check_columns(out, "offres")
    return out


def run() -> pd.DataFrame:
    if not FILES["offres"].exists():
        raise RuntimeError(
            "offres.parquet absent : lancer d'abord scripts/classify_offres.py (T13)."
        )
    offres = pd.read_parquet(FILES["offres"])
    if not offres["match_methode"].eq(MATCH_TODO).any():
        log.warning("Aucune ligne « %s » : rapprochement déjà fait ?", MATCH_TODO)
    ent = pd.read_parquet(FILES["entreprises"])
    out = complete_matches(offres, ent)
    out.to_parquet(FILES["offres"], index=False)
    log.info("\n%s", match_report(out).to_string())
    return out
