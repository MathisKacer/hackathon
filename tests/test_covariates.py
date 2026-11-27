"""Tests du score v1 (T69) : régression avec covariables, a posteriori, caractéristiques."""

import numpy as np
import pandas as pd
import pytest

from radar.score.covariates import CovariateModel, design


def _firms(n=20_000, seed=0):
    rng = np.random.default_rng(seed)
    f = pd.DataFrame(
        {
            "effectif_entreprise": rng.lognormal(3.5, 1.0, n),
            "n_etab": rng.integers(1, 5, n),
            "age_ans": rng.uniform(0, 40, n),
            "n_modif_capital": rng.poisson(0.3, n),
            "augmentation_capital": rng.random(n) < 0.05,
            "densite_data": rng.poisson(5, n),
            "ess": False,
            "societe_mission": False,
            "categorie": "PME",
            "naf_division": rng.choice(["62", "47", "69"], n, p=[0.2, 0.5, 0.3]),
        },
        index=[f"{i:09d}" for i in range(n)],
    )
    f["E"] = f["effectif_entreprise"] / 100
    return f


def test_recovers_simulated_effects():
    """Étude de simulation : effets vrais connus (capital ×1,5, densité ×1,4, secteur 62 ×8)."""
    f = _firms()
    rng = np.random.default_rng(1)
    log_mu = (
        -3.0
        + np.log(1.5) * np.log1p(f["n_modif_capital"])
        + np.log(1.4) * np.log1p(f["densite_data"])
        + np.log(8.0) * (f["naf_division"] == "62")
    )
    lam = rng.gamma(2.0, np.exp(log_mu) / 2.0)  # surdispersion : φ = 0,5
    f["k"] = rng.poisson(lam * f["E"])
    m = CovariateModel().fit(f)
    p = m.res.params
    assert np.exp(p["log_modif_capital"]) == pytest.approx(1.5, rel=0.25)
    assert np.exp(p["log_densite_data"]) == pytest.approx(1.4, rel=0.15)
    assert np.exp(p["naf_62"] - p["naf_47"]) == pytest.approx(8.0, rel=0.3)
    assert m.phi == pytest.approx(0.5, rel=0.5)


def test_posterior_uses_offers_and_falls_back_to_prior():
    f = _firms(5_000)
    f["k"] = np.random.default_rng(2).poisson(0.05 * f["E"])
    m = CovariateModel().fit(f)
    g = f.iloc[[0, 0, 0]].copy()  # la même entreprise : hors zone, 0 offre, 20 offres
    g["E"] = [0.0, 10.0, 10.0]
    g["k"] = [0, 0, 20]
    post = m.posterior(g)
    assert post["intensite_post"].iloc[0] == pytest.approx(post["prior_moyenne"].iloc[0])
    assert post["intensite_post"].iloc[2] > post["intensite_post"].iloc[1]
    assert (post["intensite_ic_bas"] <= post["intensite_post"]).all()


def test_design_same_columns_for_unseen_divisions():
    f = _firms(2_000)
    _, divs = design(f)
    g = f.head(5).assign(naf_division="99")  # division inconnue → « autre », mêmes colonnes
    x1, _ = design(f, divs)
    x2, _ = design(g, divs)
    assert list(x1.columns) == list(x2.columns)


def test_bodacc_registre_parsing():
    from radar.score import features as F

    raw = pd.DataFrame(
        {
            "registre": ["499 060 473,499060473", None],
            "dateparution": ["2026-01-08", "2026-01-09"],
            "modificationsgenerales": ['{"descriptif": "capital (augmentation)"}', "x"],
        }
    )
    # même logique que capital_changes(), sans réseau
    sir = raw["registre"].map(
        lambda reg: next(
            (s for s in str(reg).replace(" ", "").split(",") if len(s) == 9 and s.isdigit()),
            None,
        )
    )
    assert sir.iloc[0] == "499060473" and pd.isna(sir.iloc[1])
    assert hasattr(F, "capital_changes")


def test_one_sided_update_never_below_prior():
    """D33 : « 0 offre » ne fait pas descendre sous l'a priori ; une offre fait monter."""
    f = _firms(5_000)
    f["k"] = np.random.default_rng(3).poisson(0.05 * f["E"])
    m = CovariateModel().fit(f)
    g = f.iloc[[0, 0]].copy()
    g["E"] = [50.0, 50.0]
    g["k"] = [0, 5]
    post = m.posterior(g)
    assert post["intensite_post"].iloc[0] == pytest.approx(post["prior_moyenne"].iloc[0])
    assert post["intensite_post"].iloc[1] > post["prior_moyenne"].iloc[1]
    m.one_sided = False  # bayésien classique : 0 offre sur une grosse exposition fait descendre
    assert m.posterior(g)["intensite_post"].iloc[0] < post["prior_moyenne"].iloc[0]
