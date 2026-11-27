"""Construction de data/processed/offres.parquet (contrat « offres »).

offres brutes (toutes sources) → domaine (radar.domains.classify, T6 d'Emma)
                               → contrat (titre + champ contrat de la source)
                               → rapprochement SIRET (T21)
"""

from __future__ import annotations

import logging

import pandas as pd

from radar.config import FILES
from radar.domains import classify
from radar.process.match_siret import match_offers, match_report
from radar.process.quick_filter import contract_from_title, load_raw_offers
from radar.schemas import check_columns

log = logging.getLogger(__name__)


def _contrat(titre: str | None, contrat_brut: str | None) -> str:
    """stage / alternance / emploi. Le titre prime ; sinon le champ de la source."""
    from_title = contract_from_title(titre)
    if from_title != "emploi":
        return from_title
    brut = (contrat_brut or "").lower() if isinstance(contrat_brut, str) else ""
    if "apprenti" in brut or "altern" in brut or "professionnalisation" in brut:
        return "alternance"
    if "stage" in brut or "intern" in brut:
        return "stage"
    return "emploi"


def build_offres(raw: pd.DataFrame, entreprises: pd.DataFrame) -> pd.DataFrame:
    df = raw.drop_duplicates(["source", "offre_id"]).copy()
    df["domaine"] = [classify(t, r) for t, r in zip(df["titre"], df["code_rome"], strict=True)]
    df["contrat"] = [_contrat(t, c) for t, c in zip(df["titre"], df["contrat_brut"], strict=True)]
    df = match_offers(df, entreprises)
    # Une source qui fournit le SIRET (La bonne alternance) prime sur le rapprochement.
    if "siret" in df:
        has = df["siret"].notna()
        df.loc[has, "siret_match"] = df.loc[has, "siret"]
        df.loc[has, "siren_match"] = df.loc[has, "siret"].str[:9]
        df.loc[has, ["match_methode", "match_confiance", "match_score"]] = [
            "source",
            "haute",
            100.0,
        ]
    check_columns(df, "offres")
    return df


def run() -> pd.DataFrame:
    raw = load_raw_offers()
    if raw.empty:
        raise RuntimeError("Aucune offre dans data/raw/offres_raw/ (lancer un collecteur).")
    ent = pd.read_parquet(FILES["entreprises"])
    df = build_offres(raw, ent)
    df.to_parquet(FILES["offres"], index=False)
    log.info("\n%s", match_report(df).to_string())
    return df
