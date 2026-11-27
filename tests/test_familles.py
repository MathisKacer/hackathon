"""Familles de marque (T26), sans réseau."""

import pandas as pd

from radar.familles import brand_key, build_families, family_signal, mark_family_offers


def test_brand_key():
    assert brand_key("THALES SIX GTS FRANCE SAS") == "thales"
    assert brand_key("Safran Electrical & Power") == "safran"
    assert brand_key("CREDIT MUTUEL ARKEA") == "credit mutuel"  # 1er mot générique → 2 mots
    assert brand_key("SAINT-GOBAIN SEVA") == "saint gobain"
    assert brand_key("SOCIETE GENERALE") is None  # deux mots génériques : pas de marque
    assert brand_key("SOCIETE CADI") == "societe cadi"
    assert brand_key("AB") is None
    assert brand_key(None) is None


def _data():
    ent = pd.DataFrame(
        {
            "siren": ["1", "2", "3", "4", "5", "6"],
            "nom": [
                "THALES SIX GTS",
                "THALES SIMULATION",
                "THALES INTERNATIONAL",
                "THALES BOULANGERIE",  # PME : hors familles
                "SAFRAN AI",  # seul de sa marque parmi les ETI/GE : pas de famille
                "SOCIETE GENERALE",
            ],
            "categorie": ["GE", "ETI", "GE", "PME", "GE", "GE"],
        }
    )
    sc = pd.DataFrame(
        {
            "siren": ["1", "2", "3", "5"],
            "domaine": "data",
            "n_offres_domaine_siren": [3, 0, 1, 2],
            "n_stage_domaine_siren": [2, 0, 0, 1],
            "n_alternance_domaine_siren": [0, 0, 1, 0],
        }
    )
    return ent, sc


def test_build_families():
    fam = build_families(*_data())
    assert sorted(fam["siren"]) == ["1", "2", "3"]
    assert set(fam["famille"]) == {"thales"} and set(fam["famille_nom"]) == {"Thales"}
    assert (fam["famille_n_societes"] == 3).all()


def test_mark_family_offers_counts_sisters_for_the_contract():
    fam = build_families(*_data())
    df = pd.DataFrame({"siren": ["2", "3", "4", "9"]})
    stage = mark_family_offers(df, fam, "Stage").set_index("siren")
    assert stage.loc["2", "famille_offres"] == 2  # le stage de la sœur n°1
    assert stage.loc["3", "famille_offres"] == 2
    assert stage.loc["4", "famille_offres"] == 0  # PME homonyme : pas reliée
    assert stage.loc["9", "famille_offres"] == 0
    alt = mark_family_offers(df, fam, "Alternance").set_index("siren")
    assert alt.loc["2", "famille_offres"] == 1 and alt.loc["3", "famille_offres"] == 0
    tous = mark_family_offers(df, fam, "Tous").set_index("siren")
    assert tous.loc["2", "famille_offres"] == 4
    assert tous.loc["2", "famille_societes_avec_offre"] == 2


def test_empty_and_signal():
    out = mark_family_offers(pd.DataFrame({"siren": ["1"]}), pd.DataFrame(), "Stage")
    assert out["famille_offres"].tolist() == [0]
    assert family_signal({"famille_nom": "Thales", "famille_offres": 3}) == (
        "Groupe Thales : 3 offres déjà publiées"
    )
    assert family_signal({"famille_offres": 0}) == ""


def test_fake_scores_without_siren_columns():
    """T75 : scores factices = comptes par site, sans `siren` ni colonnes `*_siren`."""
    ent, _ = _data()
    ent = ent.assign(siret=[s + "0001" for s in ent["siren"]])
    extra = pd.DataFrame({"siren": ["1"], "nom": ["THALES SIX GTS"], "categorie": ["GE"]})
    ent = pd.concat([ent, extra.assign(siret="10002")], ignore_index=True)  # 2e site de 1
    sc = pd.DataFrame(
        {
            "siret": ["10001", "10002", "20001", "30001"],
            "domaine": "data",
            "n_offres_domaine": [2, 1, 0, 1],
            "n_stage_domaine": [1, 1, 0, 0],
            "n_alternance_domaine": [0, 0, 0, 1],
        }
    )
    fam = build_families(ent, sc).set_index("siren")
    assert fam.loc["1", "n_offres_domaine_siren"] == 3  # deux sites additionnés
    assert fam.loc["1", "n_stage_domaine_siren"] == 2
    out = mark_family_offers(pd.DataFrame({"siren": ["2"]}), fam.reset_index(), "Stage")
    assert out["famille_offres"].tolist() == [2]
