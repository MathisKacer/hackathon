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


def test_source_columns_like_real_collectors(data):
    """T19 : chaque fichier factice a exactement les colonnes du vrai collecteur, dans l'ordre."""
    from radar.collect import adzuna, lba

    assert list(data.offres_raw["adzuna"].columns) == adzuna.COLUMNS
    assert list(data.offres_raw["lba"].columns) == lba.COLUMNS
    # les offres « traitées » gardent toutes les colonnes, comme classify_offres
    assert set(adzuna.COLUMNS) | set(lba.COLUMNS) <= set(data.offres.columns)


def test_adzuna_region_requete(data):
    """T19 : la région de la requête, comme Adzuna (libellés de collect/adzuna.py)."""
    from radar.collect.adzuna import REGIONS
    from radar.geo import region_of

    adz = data.offres_raw["adzuna"]
    assert adz["region_requete"].notna().all()
    assert set(adz["region_requete"]) <= set(REGIONS)
    assert (adz["region_requete"] == adz["code_postal"].str[:2].map(region_of)).all()
    assert adz["zone"].str.startswith("France > ").all()
    assert (adz["requete"] == "data").all()
    assert (adz["salaire_min"].dropna() <= adz.loc[adz["salaire_min"].notna(), "salaire_max"]).all()


def test_lba_columns_formats(data):
    """T19 : formats de l'API La bonne alternance (spec OpenAPI), utiles à T67 (niveau d'études)."""
    lba = data.offres_raw["lba"]
    assert set(lba["niveau_diplome"].dropna()) <= {"3", "4", "5", "6", "7"}
    assert lba["niveau_diplome"].notna().mean() >= 0.7  # ~10 % non renseigné
    assert set(lba["teletravail"].dropna()) <= {"onsite", "hybrid", "remote"}
    assert (lba["statut"] == "Active").all()
    assert not lba["delegue_ecole"].any()  # le SIRET factice est celui de l'entreprise
    ent = data.entreprises.set_index("siret")
    assert (lba["naf"] == lba["siret"].map(ent["naf"])).all()
    assert set(lba["duree_mois"].dropna()) <= {12, 24, 36}
    assert (pd.to_datetime(lba["date_expiration"]) > pd.to_datetime(lba["date_publication"])).all()


def test_source_columns_do_not_change_other_columns():
    """Les colonnes propres aux sources ont leur propre générateur : le reste ne bouge pas."""
    import numpy as np

    from radar.fake_data import OFFRES_RAW, make_entreprises, make_offres

    ent = make_entreprises(np.random.default_rng(3), 300)
    day = pd.Timestamp("2026-11-27").date()
    a = make_offres(np.random.default_rng(5), ent, day, np.random.default_rng(1))[1]
    b = make_offres(np.random.default_rng(5), ent, day, np.random.default_rng(2))[1]
    assert a[OFFRES_RAW].equals(b[OFFRES_RAW])
    assert not a["niveau_diplome"].equals(b["niveau_diplome"])
