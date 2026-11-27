"""Candidature spontanée sans recherche (T78), sans réseau."""

import pandas as pd

from radar.candidature import candidature_facts, level_words, matching_offers


def _row(**kw):
    base = {
        "n_offres_domaine_siren": 3,
        "n_stage_domaine_siren": 0,
        "n_alternance_domaine_siren": 1,
        "c_intensite": 0.93,
        "c_embauche": 0.55,
    }
    return pd.Series({**base, **kw})


def test_level_words():
    assert level_words(0.93) == "très élevé (plus que 93 % des entreprises)"
    assert level_words(0.2).startswith("faible")
    assert level_words(None) is None


def test_matching_offers_by_contract():
    assert matching_offers(_row(), "Stage") == (0, 3)
    assert matching_offers(_row(), "Alternance") == (1, 3)
    assert matching_offers(_row(), "Emploi") == (2, 3)
    assert matching_offers(_row(), "Tous") == (3, 3)
    # scores factices : colonnes par site
    assert matching_offers(pd.Series({"n_offres_domaine": 2, "n_stage_domaine": 2}), "Stage") == (
        2,
        2,
    )


def test_verdicts():
    stage = candidature_facts(_row(), "Stage", "data")
    assert "opportunité cachée" in stage["verdict"]
    alt = candidature_facts(_row(), "Alternance", "data")
    assert alt["verdict"].startswith("L'entreprise publie déjà 1 offre d'alternance en data")
    none = candidature_facts(
        _row(n_offres_domaine_siren=0, n_alternance_domaine_siren=0), "Stage", "data"
    )
    assert none["verdict"].startswith("Candidature spontanée possible")
    assert any("Besoin en data : très élevé" in line for line in stage["lignes"])


def test_lba_and_group_lines():
    f = candidature_facts(
        _row(),
        "Alternance",
        "data",
        recruteur_lba=True,
        groupe="Groupe Thales : 3 offres déjà publiées",
    )
    assert any("La bonne alternance" in line for line in f["lignes"])
    assert f["lignes"][-1] == "Groupe Thales : 3 offres déjà publiées — regarde aussi ses offres."
    assert not any(
        "La bonne alternance" in line
        for line in candidature_facts(_row(), "Stage", "data", recruteur_lba=True)["lignes"]
    )
