"""T13 — Classifieur d'offres (radar/process/classify.py), sans réseau."""

import pandas as pd
import pytest

from radar.fake_data import generate
from radar.process.classify import (
    MATCH_FROM_SOURCE,
    MATCH_SCHOOL,
    MATCH_TODO,
    classify_offers,
    contract_with_rule,
)
from radar.schemas import OFFRES_RAW


@pytest.mark.parametrize(
    "title,brut,expected",
    [
        ("Data Analyst", "Apprentissage", ("alternance", "contrat_brut")),
        ("Data Analyst", "Professionnalisation", ("alternance", "contrat_brut")),
        ("Alternance - Data Engineer", None, ("alternance", "titre")),
        ("Apprenti(e) statisticien", "permanent", ("alternance", "titre")),
        ("Stage ou alternance - Data", None, ("alternance", "titre")),
        ("Stage - Data Scientist", "contract", ("stage", "titre")),  # le titre l'emporte
        ("Stagiaire data", None, ("stage", "titre")),
        ("Data Science Internship", None, ("stage", "titre")),
        ("Graduate trainee - Finance", None, ("stage", "titre")),
        ("PFE - Machine learning", None, ("stage", "titre")),
        ("Médecin interne", None, ("emploi", "defaut")),  # « interne » ≠ internship
        ("Data Engineer Senior", "permanent", ("emploi", "defaut")),
        (None, None, ("emploi", "defaut")),
    ],
)
def test_contract_rules(title, brut, expected):
    assert contract_with_rule(title, brut) == expected


def _raw(**cols):
    n = len(next(iter(cols.values())))
    base = {c: [None] * n for c in OFFRES_RAW}
    base.update(cols)
    return pd.DataFrame(base)


def test_classify_offers_domain_contract_and_siret():
    raw = _raw(
        source=["lba", "lba", "adzuna", "adzuna"],
        offre_id=["1", "2", "3", "3"],  # doublon Adzuna
        titre=["Alternance Data Analyst", "Alternance comptable", "Stage - Data Scientist"] * 1
        + ["Stage - Data Scientist"],
        code_rome=["M1419", "M1203", None, None],
        contrat_brut=["Apprentissage", "Apprentissage", None, None],
        siret=["12345678900011", "98765432100019", None, None],
    )
    raw["delegue_ecole"] = [False, True, None, None]
    out = classify_offers(raw)

    assert len(out) == 3  # doublon supprimé
    assert out["domaine"].tolist() == ["data", "finance", "data"]
    assert out["domaine_regle"].tolist() == ["rome", "rome", "titre"]
    assert out["contrat"].tolist() == ["alternance", "alternance", "stage"]
    assert out["match_methode"].tolist() == [MATCH_FROM_SOURCE, MATCH_SCHOOL, MATCH_TODO]
    assert out["siret_match"].tolist()[0] == "12345678900011"
    assert out["siret_match"].isna().tolist() == [False, True, True]  # SIRET d'école exclu
    assert out["match_score"].tolist()[0] == 100.0


def test_runs_on_fake_raw_offers():
    data = generate(n_entreprises=300, seed=3)
    raw = pd.concat(data.offres_raw.values(), ignore_index=True)
    out = classify_offers(raw)
    assert len(out) == len(raw)
    assert set(out["contrat"]) <= {"stage", "alternance", "emploi"}
    # Les titres factices « Stage - … » / « Alternance - … » sont bien reconnus.
    agree = (
        out["contrat"] == data.offres.set_index("offre_id").loc[out["offre_id"], "contrat"].values
    )
    assert agree.mean() > 0.99
    # Les offres La bonne alternance ont leur SIRET, les offres Adzuna attendent T21.
    assert (out.loc[out["source"] == "lba", "match_methode"] == MATCH_FROM_SOURCE).all()
    assert (out.loc[out["source"] == "adzuna", "match_methode"] == MATCH_TODO).all()
