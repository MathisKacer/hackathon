"""T5 — Le générateur factice respecte le contrat de données (docs/ARCHITECTURE.md)."""

import pytest

from radar.fake_data import DOMAINS, generate, luhn_ok
from radar.schemas import CONTRATS, check_columns


@pytest.fixture(scope="module")
def data():
    return generate(n_entreprises=400, seed=0)


def test_all_tables_follow_contract(data):
    for src, df in data.offres_raw.items():
        check_columns(df, "offres_raw")
        assert (df["source"] == src).all()
    for name in ("offres", "entreprises", "scores", "candidatures_simulees", "p_reponse"):
        check_columns(getattr(data, name), name)


def test_sirets_are_valid_and_unique(data):
    e = data.entreprises
    assert e["siret"].is_unique
    assert e["siret"].map(luhn_ok).all() and e["siren"].map(luhn_ok).all()
    assert (e["siret"].str[:9] == e["siren"]).all()


def test_offers_link_to_companies(data):
    o = data.offres
    assert set(o["contrat"]) <= set(CONTRATS)
    assert set(o["siret_match"].dropna()) <= set(data.entreprises["siret"])
    assert o.loc[o["source"] == "lba", "siret"].notna().all()  # LBA gives the SIRET
    assert o.loc[o["source"] == "adzuna", "siret"].isna().all()  # Adzuna does not


def test_scores_one_row_per_siret_domain(data):
    s = data.scores
    assert not s.duplicated(["siret", "domaine"]).any()
    assert len(s) == len(data.entreprises) * len(DOMAINS)
    for col in ("c_intensite", "c_dynamisme", "c_embauche"):
        assert s[col].between(0, 1).all()
    assert (s["intensite_ic_bas"] <= s["intensite_post"]).all()
    assert (s["intensite_post"] <= s["intensite_ic_haut"]).all()


def test_reproducible():
    a = generate(n_entreprises=100, seed=7).entreprises
    b = generate(n_entreprises=100, seed=7).entreprises
    assert a.equals(b)
