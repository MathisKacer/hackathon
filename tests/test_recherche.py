"""Tests de la recherche d'entreprises (page « Entreprises »)."""

import pandas as pd

from radar.recherche import load_index, normalize, search_companies


def _index(tmp_path):
    p = tmp_path / "entreprises.parquet"
    pd.DataFrame(
        {
            "siret": ["11111111100011", "11111111100029", "22222222200022", "33333333300033"],
            "siren": ["111111111", "111111111", "222222222", "333333333"],
            "nom": ["SOPRA STERIA GROUP", "SOPRA STERIA GROUP", "SOPRA", "SOCIÉTÉ GÉNÉRALE"],
            "nom_etablissement": [None, "AGENCE RENNES", None, None],
            "sigle": [None, None, None, "SG"],
            "commune": ["COURBEVOIE", "RENNES", "MONTAUBAN", "PARIS"],
            "code_postal": ["92400", "35000", "82000", "75009"],
            "effectif_estime": [3000.0, 300.0, 30.0, 5000.0],
        }
    ).to_parquet(p)
    return load_index(p)


def test_normalize():
    assert normalize("Société Générale !") == "societe generale"
    assert normalize(None) == ""


def test_exact_and_typos(tmp_path):
    idx = _index(tmp_path)
    for q in ("sopra steria", "SOPRA-STERIA", "sopra steira", "spora steria"):
        out = search_companies(idx, q)
        assert out["nom"].iloc[0] == "SOPRA STERIA GROUP", q
    # « sopra steria » ne remonte pas « SOPRA » seul (un seul des deux mots)
    assert "SOPRA" not in set(search_companies(idx, "sopra steira")["nom"])


def test_accents_sigle_and_size_order(tmp_path):
    idx = _index(tmp_path)
    assert search_companies(idx, "societe generale")["siren"].tolist() == ["333333333"]
    assert search_companies(idx, "sg")["siren"].tolist() == ["333333333"]
    # même note : le plus gros établissement d'abord
    assert search_companies(idx, "sopra steria")["siret"].iloc[0] == "11111111100011"


def test_city_filter(tmp_path):
    idx = _index(tmp_path)
    assert search_companies(idx, "sopra steria", "rennes")["siret"].tolist() == ["11111111100029"]
    assert search_companies(idx, "sopra steria", "35")["siret"].tolist() == ["11111111100029"]
    assert search_companies(idx, "sopra steria", "lyon").empty


def test_siren_siret_and_empty(tmp_path):
    idx = _index(tmp_path)
    assert len(search_companies(idx, "111 111 111")) == 2
    assert search_companies(idx, "22222222200022")["nom"].tolist() == ["SOPRA"]
    out = search_companies(idx, "zzzzqqq")
    assert out.empty and "_score" in out.columns
    assert search_companies(idx, "   ").empty
    assert search_companies(load_index(tmp_path / "absent.parquet"), "sopra").empty


def test_with_companies_puts_whole_company_first(tmp_path):
    from radar.recherche import with_companies

    idx = _index(tmp_path)
    out = with_companies(search_companies(idx, "sopra steria"))
    assert out["_type"].tolist() == ["entreprise", "site", "site"]
    assert out["siren"].iloc[0] == "111111111" and out["_n_sites"].iloc[0] == 2
    # une entreprise à un seul site n'a pas de ligne « entreprise »
    assert with_companies(search_companies(idx, "societe generale"))["_type"].tolist() == ["site"]
    assert with_companies(search_companies(idx, "zzzzqqq")).empty


def test_with_companies_keeps_exact_single_site_match_first(tmp_path):
    """« AVISIA » (un seul site) passe devant « AVIS LOCATION » (plusieurs sites, moins proche)."""
    from radar.recherche import with_companies

    p = tmp_path / "entreprises.parquet"
    pd.DataFrame(
        {
            "siret": ["44444444400011", "55555555500011", "55555555500029"],
            "siren": ["444444444", "555555555", "555555555"],
            "nom": ["AVISIA", "AVIS LOCATION", "AVIS LOCATION"],
            "commune": ["PARIS", "NICE", "LYON"],
            "code_postal": ["75008", "06000", "69000"],
            "effectif_estime": [30.0, 500.0, 400.0],
        }
    ).to_parquet(p)
    out = with_companies(search_companies(load_index(p), "avisia"))
    assert out["nom"].tolist() == ["AVISIA", "AVIS LOCATION", "AVIS LOCATION", "AVIS LOCATION"]
    assert out["_type"].tolist() == [
        "site",
        "entreprise",
        "site",
        "site",
    ]  # entreprise avant ses sites
