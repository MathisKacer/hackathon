"""Score pondéré de la couche orange (T42), sans réseau."""

import numpy as np
import pandas as pd
import pytest

from radar.spontaneous import (
    COMPONENTS,
    DEFAULT_WEIGHTS,
    add_user_components,
    rank_spontaneous,
    spontaneous_score,
    weighted_score,
)
from tests.test_spontaneous import RENNES, _scores


def test_defaults_cover_every_component():
    assert set(DEFAULT_WEIGHTS) == set(COMPONENTS)


def test_user_components():
    df = _scores(distance_km=[0.0, 10.0, 5.0, 20.0, 15.0])
    out = add_user_components(df, radius_km=20, contrat="Stage")
    assert out["c_proximite"].tolist() == pytest.approx([1.0, 0.5, 0.75, 0.0, 0.25])
    # EmploiData : offres du domaine, aucune en stage → opportunité cachée ; StageData : non
    assert out["c_cachee"].tolist() == [0.0, 0.0, 0.0, 1.0, 0.0]
    assert (out["c_dynamisme"] == 0.5).all()  # absent → neutre
    # « Tous » : une offre du domaine correspond toujours → pas d'opportunité cachée
    assert add_user_components(df, 20, "Tous")["c_cachee"].sum() == 0


def test_weighted_score_is_a_mean_and_apports_sum_to_score():
    df = pd.DataFrame(
        {
            "c_intensite": [1.0, 0.0],
            "c_embauche": [0.5, 0.5],
            "c_proximite": [0.0, 1.0],
            "c_cachee": [0.0, 0.0],
            "c_dynamisme": [0.5, 0.5],
        }
    )
    out = weighted_score(df, {"c_intensite": 2, "c_embauche": 1, "c_proximite": 1})
    assert out["score"].tolist() == pytest.approx([(2 + 0.5) / 4, (0.5 + 1) / 4])
    apports = out[[f"apport_{c}" for c in COMPONENTS]].sum(axis=1)
    assert apports.tolist() == pytest.approx(out["score"].tolist())
    assert out["apport_c_dynamisme"].isna().all()  # poids 0 → apport masqué


def test_all_weights_zero_falls_back_to_d13():
    df = _scores().assign(c_proximite=0.3, c_cachee=0.0, c_dynamisme=0.5)
    out = weighted_score(df, {c: 0 for c in COMPONENTS})
    assert out["score"].tolist() == pytest.approx(spontaneous_score(df).tolist())
    assert out["apport_c_intensite"].isna().all()


def test_weights_change_the_ranking():
    by_need = rank_spontaneous(_scores(), *RENNES, 20, "Tous", {"c_intensite": 1})
    assert by_need["nom"].iloc[0] == "Proche"
    by_distance = rank_spontaneous(_scores(), *RENNES, 20, "Tous", {"c_proximite": 1})
    assert np.all(np.diff(by_distance["distance_km"].to_numpy()) >= 0)
    assert by_distance["score"].between(0, 1).all()


def test_hidden_opportunity_weight_promotes_companies_with_other_offers():
    out = rank_spontaneous(_scores(), *RENNES, 20, "Stage", {"c_cachee": 5, "c_intensite": 1})
    assert out["nom"].iloc[0] == "EmploiData"


def test_rank_without_city_ignores_proximity():
    """T93 (essai) : sans ville, pas de distance ni de proximité, mais un classement quand même."""
    import pandas as pd

    from radar.spontaneous import DEFAULT_WEIGHTS, rank_spontaneous

    df = pd.DataFrame(
        {
            "siret": ["1", "2"],
            "lat": [48.1, 43.6],
            "lon": [-1.6, 1.4],
            "c_intensite": [0.9, 0.2],
            "c_embauche": [0.8, 0.3],
            "n_offres_domaine": [0, 0],
            "n_stage_domaine": [0, 0],
            "n_alternance_domaine": [0, 0],
        }
    )
    out = rank_spontaneous(df, None, None, None, "stage", DEFAULT_WEIGHTS)
    assert list(out["siret"]) == ["1", "2"]
    assert out["distance_km"].isna().all()
    assert out["apport_c_proximite"].isna().all()  # proximité ignorée
