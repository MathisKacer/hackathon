"""Tests de l'enrichissement SIRENE (sans réseau)."""

import pandas as pd

from radar.collect.sirene import enrich
from radar.schemas import SCHEMAS


def _sample() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "siret": ["11111111100011", "22222222200022"],
            "siren": ["111111111", "222222222"],
            "nom": ["ACME", "BETA"],
            "naf": ["62.02A", "70.22Z"],
            "naf_libelle": ["Conseil en systèmes et logiciels informatiques", "Conseil"],
            "tranche_effectif": ["12", "53"],
            "categorie": ["PME", "GE"],
            "lat": [48.1, None],
            "lon": [-1.6, None],
            "commune": ["RENNES", "SAINT-DENIS"],
            "code_commune": ["35238", "97411"],
        }
    )


def test_enrich_respects_contract():
    out = enrich(_sample())
    assert set(SCHEMAS["entreprises"]) <= set(out.columns)


def test_effectif_estimate_and_departement():
    out = enrich(_sample())
    assert out.loc[0, "effectif_min"] == 20 and out.loc[0, "effectif_max"] == 49
    assert out.loc[0, "effectif_estime"] == round((20 * 49) ** 0.5)
    assert out["departement"].tolist() == ["35", "974"]  # DOM sur 3 caractères


def test_placeholders_are_missing_not_false():
    out = enrich(_sample())
    # Pas encore alimentées : manquantes, pas « False » / 0 (sinon biais dans le score)
    assert out["procedure_collective"].isna().all()
    assert out["ca_n"].isna().all() and out["lbb_proba"].isna().all()
