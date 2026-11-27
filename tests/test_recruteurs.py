"""Recruteurs LBA dans la couche orange (T51), sans réseau."""

import pandas as pd
import pytest

from radar.recruteurs import domain_rome_codes, lba_recruiter_sirets, mark_lba_recruiters
from radar.spontaneous import (
    COMPONENTS,
    DEFAULT_WEIGHTS,
    add_user_components,
    applicable_weights,
    rank_spontaneous,
)
from tests.test_spontaneous import RENNES, _scores


@pytest.fixture
def rec_file(tmp_path):
    df = pd.DataFrame(
        {
            "siret": ["1", "2", "3", "4"],
            "code_rome": ["M1405,K2303", "K2303, M1811", "K2303,M1201", None],
        }
    )
    path = tmp_path / "lba_recruteurs.parquet"
    df.to_parquet(path)
    return path


def test_domain_codes_are_unambiguous_only():
    codes = domain_rome_codes("data")
    assert "M1405" in codes and "M1811" in codes
    assert "M1201" not in codes  # rome_partiel (analyste financier) : ambigu, exclu
    assert domain_rome_codes("inconnu") == []


def test_lba_recruiter_sirets(rec_file):
    # 1 : M1405 ; 2 : M1811 (espace) ; 3 : code ambigu seul ; 4 : sans code ; 9 : absent
    assert lba_recruiter_sirets(["1", "2", "3", "4", "9"], "data", rec_file) == {"1", "2"}
    assert lba_recruiter_sirets(["1"], "inconnu", rec_file) == set()
    assert lba_recruiter_sirets(["1"], "data", rec_file.with_name("absent.parquet")) == set()


def test_mark_lba_recruiters(rec_file):
    out = mark_lba_recruiters(pd.DataFrame({"siret": ["1", "3"]}), "data", rec_file)
    assert out["recruteur_lba"].tolist() == [True, False]
    assert "recruteur_lba" in mark_lba_recruiters(pd.DataFrame(), "data", rec_file)


def test_component_only_for_alternance_and_tous():
    df = _scores(distance_km=1.0, recruteur_lba=[True, False, True, False, False])
    alt = add_user_components(df, 20, "Alternance")["c_recruteur_lba"].tolist()
    assert alt == [1.0, 0.0, 1.0, 0.0, 0.0]
    assert add_user_components(df, 20, "Tous")["c_recruteur_lba"].sum() == 2
    assert add_user_components(df, 20, "Stage")["c_recruteur_lba"].sum() == 0
    assert (
        add_user_components(_scores(distance_km=1.0), 20, "Alternance")["c_recruteur_lba"].sum()
        == 0
    )  # colonne absente → 0


def test_applicable_weights():
    assert "c_recruteur_lba" not in applicable_weights(DEFAULT_WEIGHTS, "Stage")
    assert "c_cachee" not in applicable_weights(DEFAULT_WEIGHTS, "Tous")
    assert set(applicable_weights(DEFAULT_WEIGHTS, "Alternance")) == set(COMPONENTS)


def test_lba_recruiter_promoted_in_alternance_ignored_in_stage():
    df = _scores(recruteur_lba=[False, False, False, False, True])  # « Moyenne » est recruteur
    w = {"c_intensite": 1, "c_recruteur_lba": 5}
    alt = rank_spontaneous(df, *RENNES, 20, "Alternance", w)
    assert alt["nom"].iloc[0] == "Moyenne"
    stage = rank_spontaneous(df, *RENNES, 20, "Stage", w)
    assert stage["nom"].iloc[0] != "Moyenne"
    assert stage["apport_c_recruteur_lba"].isna().all()  # masqué en stage
