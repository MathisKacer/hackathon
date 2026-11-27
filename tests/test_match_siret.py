"""Tests du rapprochement offres → SIRET (sans réseau, sur un mini-référentiel)."""

import pandas as pd

from radar.process.match_siret import is_intermediary, match_offers, normalize
from radar.process.offres import complete_matches

ENT = pd.DataFrame(
    {
        "siret": ["10000000000001", "10000000000002", "20000000000001", "30000000000001",
                  "40000000000001", "50000000000001", "60000000000001"],
        "siren": ["100000000", "100000000", "200000000", "300000000", "400000000", "500000000",
                  "600000000"],
        "nom": ["CAPGEMINI TECHNOLOGY SERVICES", "CAPGEMINI TECHNOLOGY SERVICES", "FRANCE AIR",
                "ELECTRICITE DE FRANCE", "ACME ANALYTICS", "LE CASINO", "INTERIM PLUS"],
        "sigle": [None, None, None, "EDF", None, None, None],
        "categorie": ["GE", "GE", "PME", "GE", "PME", "PME", "PME"],
        "naf": ["62.02A", "62.02A", "28.25Z", "35.11Z", "62.01Z", "92.00Z", "78.20Z"],
        "effectif_estime": [1400, 300, 30, 60000, 30, 14, 30],
        "lat": [48.11, 45.76, 48.92, 48.87, 48.11, 43.0, 48.11],  # Rennes, Lyon, …
        "lon": [-1.68, 4.84, 2.25, 2.33, -1.68, 3.0, -1.68],
    }
)  # fmt: skip
RENNES = (48.11, -1.68)


def _offer(name, lat=RENNES[0], lon=RENNES[1]):
    return {"offre_id": name or "x", "entreprise_nom": name, "lat": lat, "lon": lon}


def _match(*offers):
    return match_offers(pd.DataFrame(list(offers)), ENT).set_index("offre_id")


def test_normalize_keeps_france_and_drops_legal_forms():
    assert normalize("Air France SA") == "air france"
    assert normalize("France Air") == "france air"
    assert normalize("Crédit Mutuel Arkéa") == normalize("CREDIT MUTUEL ARKEA")
    assert normalize(None) == "" and normalize(float("nan")) == ""


def test_intermediaries():
    assert is_intermediary("Collective.work", normalize("Collective.work"))
    assert is_intermediary("Randstad professional", normalize("Randstad professional"))
    assert is_intermediary("Cabinet XYZ Recrutement", normalize("Cabinet XYZ Recrutement"))
    assert not is_intermediary("Air Liquide", normalize("Air Liquide"))


def test_prefix_picks_nearest_establishment():
    r = _match(_offer("Capgemini"))
    assert r.loc["Capgemini", "siret_match"] == "10000000000001"  # Rennes, pas Lyon
    assert r.loc["Capgemini", "match_methode"] == "prefixe"


def test_no_confusion_air_france_france_air():
    r = _match(_offer("Air France"))
    assert pd.isna(r.loc["Air France", "siret_match"])


def test_sigle_only_for_big_companies():
    r = _match(_offer("EDF"))
    assert r.loc["EDF", "siret_match"] == "30000000000001"
    assert r.loc["EDF", "match_methode"].startswith("sigle")


def test_far_generic_homonym_rejected():
    r = _match(_offer("Groupe Casino"))  # « le casino » à des centaines de km
    assert pd.isna(r.loc["Groupe Casino", "siret_match"])


def test_staffing_naf_is_intermediary():
    r = _match(_offer("Interim Plus"))
    assert r.loc["Interim Plus", "intermediaire"]


def test_complete_matches_only_touches_rows_to_match():
    offres = pd.DataFrame(
        {
            "offre_id": ["a", "b"],
            "entreprise_nom": ["Capgemini", "Peu importe"],
            "lat": [RENNES[0], RENNES[0]],
            "lon": [RENNES[1], RENNES[1]],
            "siret_match": [None, "99999999900011"],
            "match_score": [None, 100.0],
            "match_methode": ["a_rapprocher", "siret_source"],
        }
    )
    # Colonnes du contrat « offres » non utilisées ici : valeurs factices
    from radar.schemas import SCHEMAS

    for c in SCHEMAS["offres"]:
        if c not in offres:
            offres[c] = None
    out = complete_matches(offres, ENT).set_index("offre_id")
    assert out.loc["a", "siret_match"] == "10000000000001"
    assert out.loc["b", "siret_match"] == "99999999900011"  # SIRET de la source conservé
    assert out.loc["b", "match_methode"] == "siret_source"
    assert out.loc["b", "siren_match"] == "999999999"
