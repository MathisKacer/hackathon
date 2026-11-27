"""Couche « Candidature spontanée » (T40) et géocodage, sans réseau."""

import pandas as pd
import pytest

from radar.config import FILES
from radar.geocode import geocode, parse_response
from radar.spontaneous import bbox, haversine_km, load_nearby, rank_spontaneous

RENNES = (48.1109, -1.6837)


def _scores(**extra) -> pd.DataFrame:
    base = pd.DataFrame(
        {
            "siret": ["1", "2", "3", "4", "5"],
            "nom": ["Proche", "Loin", "StageData", "EmploiData", "Moyenne"],
            # 0,5 km, ~70 km (Saint-Brieuc), puis proches de Rennes
            "lat": [48.115, 48.514, 48.12, 48.10, 48.11],
            "lon": [-1.68, -2.765, -1.69, -1.67, -1.70],
            "c_intensite": [0.9, 1.0, 0.95, 0.8, 0.4],
            "c_embauche": [0.9, 1.0, 0.95, 0.8, 0.4],
            "n_offres_domaine": [0, 0, 2, 1, 0],
            "n_stage_domaine": [0, 0, 2, 0, 0],
            "n_alternance_domaine": [0, 0, 0, 0, 0],
        }
    )
    return base.assign(**extra)


def test_haversine_rennes_paris():
    d = haversine_km(*RENNES, [48.8566], [2.3522])[0]
    assert 300 < d < 320


def test_bbox_contains_circle():
    lat_min, lat_max, lon_min, lon_max = bbox(*RENNES, 20)
    assert haversine_km(*RENNES, [lat_max], [RENNES[1]])[0] == pytest.approx(20, rel=0.01)
    assert haversine_km(*RENNES, [RENNES[0]], [lon_max])[0] == pytest.approx(20, rel=0.01)
    assert lat_min < RENNES[0] < lat_max and lon_min < RENNES[1] < lon_max


def test_radius_and_order():
    out = rank_spontaneous(_scores(), *RENNES, radius_km=20, contrat="Tous")
    assert "Loin" not in set(out["nom"])  # hors rayon
    # Tous contrats : les entreprises avec une offre du domaine sont en bleu, pas en orange
    assert list(out["nom"]) == ["Proche", "Moyenne"]
    assert out["score"].is_monotonic_decreasing
    assert out["url_annuaire"].iloc[0].endswith("/etablissement/1")


def test_hidden_opportunity_depends_on_contract():
    # Stage visé : EmploiData a une offre data d'emploi mais aucun stage → opportunité cachée
    stage = set(rank_spontaneous(_scores(), *RENNES, 20, "Stage")["nom"])
    assert "EmploiData" in stage and "StageData" not in stage
    emploi = set(rank_spontaneous(_scores(), *RENNES, 20, "Emploi")["nom"])
    assert "StageData" in emploi and "EmploiData" not in emploi


def test_real_scores_use_siren_level_and_drop_suspects():
    df = _scores(
        n_offres_domaine_siren=[3, 0, 2, 1, 0],  # le siège de « Proche » a publié 3 stages data
        n_stage_domaine_siren=[3, 0, 2, 0, 0],
        n_alternance_domaine_siren=[0, 0, 0, 0, 0],
        volume_suspect=[False, False, False, False, True],
    )
    out = rank_spontaneous(df, *RENNES, 20, "Stage")
    assert set(out["nom"]) == {"EmploiData"}


def test_empty_input():
    out = rank_spontaneous(pd.DataFrame(), *RENNES, 20, "Stage")
    assert out.empty and "score" in out.columns


def test_load_nearby_duckdb(tmp_path):
    ent = _scores()[["siret", "nom", "lat", "lon"]].assign(commune="Rennes")
    sc = _scores().drop(columns=["nom", "lat", "lon"]).assign(domaine="data")
    other = sc.assign(domaine="finance")
    ent.to_parquet(tmp_path / "e.parquet")
    pd.concat([sc, other]).to_parquet(tmp_path / "s.parquet")
    df = load_nearby(*RENNES, 20, "data", tmp_path / "e.parquet", tmp_path / "s.parquet")
    assert set(df["domaine"]) == {"data"}
    assert "Loin" not in set(df["nom"])  # écarté par le rectangle
    assert {"commune", "lat", "lon", "c_intensite"} <= set(df.columns)


def test_parse_geoplateforme():
    payload = {
        "features": [
            {
                "geometry": {"coordinates": [-1.741779, 48.050646]},
                "properties": {"label": "51 Rue Blaise Pascal 35170 Bruz", "score": 0.95},
            }
        ]
    }
    p = parse_response(payload)
    assert (p.lat, p.lon) == (48.050646, -1.741779) and "Bruz" in p.label
    assert parse_response({"features": []}) is None


def test_geocode_network_error_returns_none():
    import requests

    class Boom:
        def get(self, *a, **k):
            raise requests.ConnectionError("hors ligne")

    assert geocode("Rennes", session=Boom()) is None
    assert geocode("  ", session=Boom()) is None


def test_files_contract_names():
    assert FILES["scores"].name == "scores.parquet"
