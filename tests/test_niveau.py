"""T67 — Niveau d'études attendu (radar/niveau.py)."""

import pandas as pd
import pytest

from radar.niveau import (
    UNKNOWN,
    add_levels,
    detect_levels,
    levels_label,
    matches_levels,
    offer_levels,
)


@pytest.mark.parametrize(
    ("text", "levels"),
    [
        ("Stage Data Analyst - Bac+5", ["7"]),
        ("profil bac +3/4", ["6"]),
        ("De Bac+3 à Bac+5", ["6", "7"]),
        ("CDI Bac5 Grande École", ["7"]),
        ("Étudiant(e) en Master 2 statistiques", ["7"]),
        ("en première année de master (M1)", ["6"]),
        ("Masters or PhD in machine learning", ["7", "8"]),
        ("Bachelor’s degree in a quantitative field", ["6"]),
        ("BTS SIO ou DUT informatique", ["5"]),
        ("MSc Data Science", ["7"]),
        ("élève d'une école d'ingénieurs", ["7"]),
        ("niveau bac minimum", ["4"]),
    ],
)
def test_detect_levels(text, levels):
    assert detect_levels(text) == levels


@pytest.mark.parametrize(
    "text",
    [
        "Master Data Manager",  # métier, pas un diplôme
        "Scrum Master confirmé",
        "Gestionnaire master données",
        "Data engineer chez Capgemini",
        "Le but de la mission",
        "Ingénieur data",  # « ingénieur » seul : le métier
        "",
    ],
)
def test_no_false_positive(text):
    assert detect_levels(text) == []


def test_offer_levels_prefers_source_field():
    """La bonne alternance donne le niveau : il prime sur le texte."""
    row = {"titre": "Alternance Bac+2", "description": None, "niveau_diplome": "7"}
    assert offer_levels(row) == "7"
    row = {"titre": "Stage Master 2 data", "description": "M1 accepté", "niveau_diplome": None}
    assert offer_levels(row) == "6,7"
    assert offer_levels({"titre": "Data analyst", "description": "SQL"}) is None


def test_levels_label():
    assert levels_label("7") == "Bac+5"
    assert levels_label("6,7") == "Bac+3/4 à Bac+5"
    assert levels_label("5,6,7") == "Bac+2 à Bac+5"
    assert levels_label(None) == UNKNOWN
    assert levels_label("") == UNKNOWN


def test_add_and_match_levels():
    offers = pd.DataFrame(
        {
            "titre": ["Stage Bac+5", "Alternance", "Data analyst", "Stage M1"],
            "description": [None, None, "SQL", None],
            "niveau_diplome": [None, "5", None, None],
        }
    )
    lv = add_levels(offers)["niveaux_etudes"]
    assert lv.tolist() == ["7", "5", None, "6"]
    assert matches_levels(lv, ["7"], keep_unknown=False).tolist() == [True, False, False, False]
    assert matches_levels(lv, ["7", "6"], keep_unknown=True).tolist() == [True, False, True, True]
    assert add_levels(pd.DataFrame()).columns.tolist() == ["niveaux_etudes"]


def test_fake_lba_offers_have_levels():
    """Les offres LBA factices (T19) donnent un niveau : l'app se teste sans vraies données."""
    from radar.fake_data import generate

    lba = add_levels(generate(n_entreprises=300, seed=1).offres_raw["lba"])
    assert lba["niveaux_etudes"].notna().mean() > 0.7
