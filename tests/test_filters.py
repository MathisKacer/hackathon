"""Filtres taille / secteur des entreprises (T41), sans réseau."""

import pandas as pd

from radar.filters import (
    SECTIONS,
    TAILLES,
    company_sections,
    filter_companies,
    naf_section,
    size_bucket,
)


def test_size_bucket():
    assert size_bucket("11") == "10–49"
    assert size_bucket("21") == "50–249"
    assert size_bucket("41") == "250–999"
    assert size_bucket("53") == "1 000 et plus"
    assert size_bucket(None) is None
    assert size_bucket("NN") is None


def test_every_tranche_ge_10_has_a_bucket():
    codes = [c for codes in TAILLES.values() for c in codes]
    assert len(codes) == len(set(codes))
    assert {"11", "12", "21", "22", "31", "32", "41", "42", "51", "52", "53"} == set(codes)


def test_naf_section_formats_and_bounds():
    assert naf_section("62.02A") == "J"
    assert naf_section("6202A") == "J"
    assert naf_section("01.11Z") == "A"
    assert naf_section("33.20A") == "C"
    assert naf_section("35.11Z") == "D"
    assert naf_section("64.19Z") == "K"
    assert naf_section("70.22Z") == "M"
    assert naf_section("99.00Z") == "U"
    assert naf_section(None) is None
    assert naf_section("xx") is None
    assert set(SECTIONS) == set("ABCDEFGHIJKLMNOPQRSTU")


def _df():
    return pd.DataFrame(
        {
            "siret": ["1", "2", "3", "4"],
            "naf": ["62.02A", "64.19Z", "10.71C", None],
            "tranche_effectif": ["11", "21", "42", "12"],
        }
    )


def test_filter_companies_empty_lists_keep_everything():
    assert len(filter_companies(_df(), [], [])) == 4
    assert len(filter_companies(_df())) == 4


def test_filter_companies_size_and_sector():
    out = filter_companies(_df(), tailles=["10–49", "50–249"])
    assert out["siret"].tolist() == ["1", "2", "4"]
    out = filter_companies(_df(), secteurs=["J", "K"])
    assert out["siret"].tolist() == ["1", "2"]  # NAF inconnu écarté dès qu'on filtre
    out = filter_companies(_df(), tailles=["50–249"], secteurs=["J", "K"])
    assert out["siret"].tolist() == ["2"]


def test_naf_section_column_has_priority():
    df = _df().assign(naf_section=["M", None, "C", "Q"])
    assert company_sections(df).tolist() == ["M", "K", "C", "Q"]


def test_filter_companies_on_empty_frame():
    assert filter_companies(pd.DataFrame(), ["10–49"], ["J"]).empty
