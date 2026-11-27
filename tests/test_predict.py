"""P(réponse) dans l'app (T37), sans réseau : p_reponse.parquet et modèle factices."""

import json

import numpy as np
import pandas as pd
import pytest

from radar.response.predict import (
    add_p_reponse,
    contracts_for,
    load_coefficients,
    load_p_reponse,
    with_distance,
)


@pytest.fixture
def p_file(tmp_path):
    p = pd.DataFrame(
        {
            "siret": ["1", "1", "2", "2", "3"],
            "domaine": ["data", "data", "data", "data", "finance"],
            "contrat_vise": ["stage", "alternance", "stage", "alternance", "stage"],
            "p_reponse": [0.2, 0.4, 0.1, 0.3, 0.9],
        }
    )
    path = tmp_path / "p_reponse.parquet"
    p.to_parquet(path)
    return path


def test_contracts_for():
    assert contracts_for("Stage") == ["stage"]
    assert contracts_for("Alternance") == ["alternance"]
    assert contracts_for("Tous") == ["stage", "alternance"]
    assert contracts_for("Emploi") == []


def test_with_distance():
    assert with_distance([0.2], [0.0], -0.15)[0] == pytest.approx(0.2)
    far = with_distance([0.2], [20.0], -0.15)[0]
    logit = np.log(0.2 / 0.8) - 0.3
    assert far == pytest.approx(1 / (1 + np.exp(-logit)))
    assert far < 0.2


def test_load_p_reponse_filters_and_averages(p_file):
    out = load_p_reponse(["1", "2", "3"], "data", ["stage"], p_file).set_index("siret")
    assert out["p_reponse_0"].to_dict() == pytest.approx({"1": 0.2, "2": 0.1})
    both = load_p_reponse(["1"], "data", ["stage", "alternance"], p_file)
    assert both["p_reponse_0"].iloc[0] == pytest.approx(0.3)
    assert load_p_reponse(["1"], "data", [], p_file).empty
    assert load_p_reponse(["1"], "data", ["stage"], p_file.with_name("absent.parquet")).empty


def test_add_p_reponse(p_file):
    df = pd.DataFrame({"siret": ["1", "2", "9"], "distance_km": [0.0, 10.0, 1.0]})
    coef = {"distance_10km": -0.15}
    out = add_p_reponse(df, "data", "Stage", coef, p_file)
    assert out["p_reponse"].iloc[0] == pytest.approx(0.2)
    assert out["p_reponse"].iloc[1] < 0.1  # plus loin → moins probable
    assert np.isnan(out["p_reponse"].iloc[2])  # SIRET inconnu du modèle
    assert add_p_reponse(df, "data", "Emploi", coef, p_file)["p_reponse"].isna().all()
    assert add_p_reponse(df, "data", "Stage", None, p_file)["p_reponse"].isna().all()


def test_load_coefficients(tmp_path):
    assert load_coefficients(tmp_path / "absent.json") is None
    path = tmp_path / "m.json"
    path.write_text(json.dumps({"coefficients": {"const": -2, "distance_10km": -0.15}}))
    assert load_coefficients(path) == {"const": -2.0, "distance_10km": -0.15}
