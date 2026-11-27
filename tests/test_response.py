"""Tests du simulateur (T35) et du modèle de réponse (T36), sur un mini-référentiel synthétique."""

import numpy as np
import pandas as pd

from radar.response import model
from radar.response.simulate import FEATURES, load_params, simulate
from radar.schemas import SCHEMAS


def _pool(n=1500, seed=1):
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "siret": [f"{i:014d}" for i in range(n)],
            "siren": [f"{i // 2:09d}" for i in range(n)],  # 2 établissements par entreprise
            "domaine": "data",
            "lat": 48.11 + rng.normal(0, 0.15, n),  # autour de Rennes
            "lon": -1.68 + rng.normal(0, 0.2, n),
            "c_intensite": rng.uniform(0, 1, n),
            "c_embauche": rng.uniform(0, 1, n),
            "log10_effectif": rng.uniform(1, 3.5, n),
            "a_offre_domaine": (rng.uniform(0, 1, n) < 0.1).astype(float),
        }
    )


def _params(**over):
    p = load_params()
    p["villes"] = [{"nom": "Rennes", "lat": 48.1173, "lon": -1.6778, "poids": 1}]
    p.update(over)
    return p


def test_simulation_contract_and_determinism():
    pool, params = _pool(), _params(n_etudiants=200)
    a, b = simulate(pool, params), simulate(pool, params)
    assert set(SCHEMAS["candidatures_simulees"]) <= set(a.columns)
    assert a["donnees_simulees"].all()
    assert a["p_vraie"].between(0, 1).all()
    assert (a["distance_km"] <= params["rayon_km"]).all()
    pd.testing.assert_frame_equal(a, b)  # graine fixe → reproductible


def test_model_recovers_simulation_rule():
    """Étude de simulation : les vrais coefficients (atténués) sont dans les IC à 95 %."""
    params = _params(n_etudiants=4000, sigma_entreprise=0.0)  # sans effet caché : pas d'atténuation
    cand = simulate(_pool(), params)
    train, test = model.split_by_student(cand)
    res = model.fit(train)
    rep = model.evaluate(res, test, params)
    rec = pd.DataFrame(rep["parametres"]).set_index("variable")
    # au plus une variable hors IC à 95 % (7 tests) ; les signes sont tous retrouvés
    assert (~rec["vrai_attenue_dans_ic"]).sum() <= 1
    assert (np.sign(rec.loc[FEATURES, "estime"]) == np.sign(rec.loc[FEATURES, "vrai"])).all()
    assert rep["auc_test"] > 0.6


def test_score_all_distance_free_and_contract():
    params = _params(n_etudiants=500)
    pool = _pool()
    res = model.fit(simulate(pool, params))
    p = model.score_all(res, pool)
    assert set(SCHEMAS["p_reponse_modele"]) <= set(p.columns)
    assert set(p["contrat_vise"]) == {"stage", "alternance"}
    assert p["p_reponse"].between(0, 1).all() and p["donnees_simulees"].all()


def test_constant_features_do_not_crash_t53():
    """T53 : scores sans Adzuna → variables constantes → pas de matrice singulière."""
    pool = _pool().assign(c_intensite=0.5, c_embauche=0.5)
    params = _params(n_etudiants=600)
    cand = simulate(pool, params)
    res = model.fit(cand)
    assert "c_intensite" not in res.params.index and "c_embauche" not in res.params.index
    p = model.score_all(res, pool)
    assert p["p_reponse"].between(0, 1).all()
    assert (p["contrib_c_intensite"] == 0).all()
    rep = model.evaluate(res, cand, params)  # les variables écartées ont une estimation vide
    assert rep["auc_test"] > 0.5
