"""T5 — Le générateur factice respecte le contrat de données (docs/ARCHITECTURE.md)."""

import pandas as pd
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


def test_recruteurs_lba(data):
    from radar.domains import load_domains

    rec = data.recruteurs_lba
    check_columns(rec, "recruteurs_lba")
    assert rec["siret"].is_unique and rec["siret"].map(luhn_ok).all()
    in_ref = rec["siret"].isin(data.entreprises["siret"])
    assert 0.6 < in_ref.mean() < 1  # surtout des entreprises du référentiel, plus des petites
    assert set(rec.loc[~in_ref, "taille"]) <= {"0-0", "1-2", "3-5", "6-9"}
    # « recruteur potentiel » = aucune offre d'alternance publiée
    with_alt = data.offres.loc[data.offres["contrat"] == "alternance", "siret_match"].dropna()
    assert not rec["siret"].isin(with_alt).any()
    # codes ROME réels, tirés de domains.yaml
    known = {c for d in load_domains().values() for c in d.rome}
    codes = rec["code_rome"].dropna().str.split(",").explode()
    assert set(codes) <= known


def test_recruiters_do_not_change_other_tables():
    """Les recruteurs sont tirés en dernier : les autres tables restent identiques (graine)."""
    a = generate(n_entreprises=200, seed=11)
    assert a.scores["c_intensite"].round(6).sum() > 0
    b = generate(n_entreprises=200, seed=11)
    assert a.offres.equals(b.offres) and a.recruteurs_lba.equals(b.recruteurs_lba)


def test_dates_are_iso_strings_like_real_collectors(data):
    """Les collecteurs réels écrivent des dates en texte : un mélange factice/réel ne casse rien."""
    for df in data.offres_raw.values():
        for col in ("date_collecte", "date_publication"):
            assert df[col].map(type).eq(str).all(), col
            assert pd.to_datetime(df[col], utc=True).notna().all()
