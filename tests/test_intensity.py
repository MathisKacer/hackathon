"""Tests du modèle gamma-Poisson bayésien empirique (T30/T31)."""

import numpy as np
import pandas as pd
import pytest

from radar.schemas import SCHEMAS
from radar.score.build import build_scores
from radar.score.intensity import clayton_kaldor, fit_priors, posterior


def test_clayton_kaldor_recovers_true_prior():
    """Étude de simulation : λ ~ Gamma(α=2, β=10) (moyenne 0,2), k ~ Poisson(λ·E)."""
    rng = np.random.default_rng(0)
    alpha, beta = 2.0, 10.0
    e = rng.uniform(1, 50, 20_000)
    lam = rng.gamma(alpha, 1 / beta, e.size)
    k = rng.poisson(lam * e)
    prior = clayton_kaldor(k, e, m_global=k.sum() / e.sum(), smoothing=0.0)
    assert prior.mean == pytest.approx(alpha / beta, rel=0.03)
    assert prior.alpha == pytest.approx(alpha, rel=0.15)


def _companies():
    return pd.DataFrame(
        {
            "naf_section": ["J"] * 4 + ["G"] * 2,
            "naf_division": ["62"] * 4 + ["47"] * 2,
            "k": [10, 1, 0, 0, 0, 1],
            "E": [10.0, 0.1, 5.0, 0.0, 5.0, 5.0],
        }
    )


def test_posterior_shrinks_small_exposure_and_ranks_evidence():
    df = posterior(_companies(), fit_priors(_companies()))
    big, small = df.iloc[0], df.iloc[1]
    # 1 offre pour 10 salariés n'égale pas 10 offres pour 1 000 : intervalle bien plus large
    assert (small["intensite_ic_haut"] - small["intensite_ic_bas"]) > (
        big["intensite_ic_haut"] - big["intensite_ic_bas"]
    )
    # Rétrécissement : l'estimation de la petite entreprise est très en dessous de k/E = 10
    assert small["intensite_post"] < 0.5 * (1 / 0.1)


def test_uncovered_company_gets_its_sector_prior():
    df = posterior(_companies(), fit_priors(_companies()))
    uncovered = df.iloc[3]  # E = 0 : région non collectée
    assert uncovered["intensite_post"] == pytest.approx(uncovered["prior_moyenne"])


def test_zero_offers_with_large_exposure_lowers_estimate():
    df = posterior(_companies(), fit_priors(_companies()))
    assert df.iloc[2]["intensite_post"] < df.iloc[3]["intensite_post"]  # même secteur


def test_build_scores_contract_and_exclusions():
    ent = pd.DataFrame(
        {
            "siret": ["10000000000001", "20000000000001", "30000000000001"],
            "siren": ["100000000", "200000000", "300000000"],
            "naf": ["62.02A", "47.11F", "78.20Z"],
            "naf_section": ["J", "G", "N"],
            "naf_division": ["62", "47", "78"],
            "effectif_estime": [100.0, 50.0, 30.0],
            "departement": ["35", "35", "35"],
        }
    )
    offres = pd.DataFrame(
        {
            "offre_id": ["a", "b"],
            "siret_match": ["10000000000001", None],
            "siren_match": ["100000000", None],
            "domaine": ["data", "data"],
            "contrat": ["stage", "emploi"],
            "intermediaire": [False, True],
        }
    )
    s = build_scores(ent, offres, {"Bretagne": 1.0}).set_index("siret")
    assert set(SCHEMAS["scores"]) <= set(s.reset_index().columns)
    assert "30000000000001" not in s.index  # intérim (NAF 78) non noté
    assert s.loc["10000000000001", "n_stage_domaine"] == 1
    assert s[["c_intensite", "c_embauche"]].stack().between(0, 1).all()
