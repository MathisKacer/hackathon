"""Tests du référentiel SIRENE (T20). Fusion des tests de Mathis et de Celia."""

import duckdb
import pandas as pd
import pytest

from radar.collect.sirene import TRANCHE_LIBELLES, TRANCHES, build_query, connect, enrich
from radar.config import FILES
from radar.schemas import SCHEMAS, check_columns


def _sample() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "siret": ["11111111100011", "22222222200022"],
            "siren": ["111111111", "222222222"],
            "nom": ["ACME", "BETA"],
            "naf": ["62.02A", "70.22Z"],
            "naf_libelle": ["Conseil en systèmes et logiciels informatiques", "Conseil"],
            "tranche_effectif": ["12", "53"],
            "categorie": ["PME", "GE"],
            "lat": [48.1, None],
            "lon": [-1.6, None],
            "commune": ["RENNES", "SAINT-DENIS"],
            "code_commune": ["35238", "97411"],
        }
    )


# --- Sans réseau -------------------------------------------------------------------------


def test_enrich_respects_contract():
    out = enrich(_sample())
    assert set(SCHEMAS["entreprises"]) <= set(out.columns)


def test_effectif_estimate_and_departement():
    out = enrich(_sample())
    assert out.loc[0, "effectif_min"] == 20 and out.loc[0, "effectif_max"] == 49
    assert out.loc[0, "effectif_estime"] == round((20 * 49) ** 0.5)
    assert out["departement"].tolist() == ["35", "974"]  # DOM sur 3 caractères


def test_tranche_libelle():
    out = enrich(_sample())
    assert out["tranche_libelle"].tolist() == ["20 à 49 salariés", "10 000 salariés et plus"]


def test_placeholders_are_missing_not_false():
    out = enrich(_sample())
    # Pas encore alimentées : manquantes, pas « False » / 0 (sinon biais dans le score)
    assert out["procedure_collective"].isna().all()
    assert out["ca_n"].isna().all() and out["lbb_proba"].isna().all()


def test_tranches_exclude_small_and_unknown():
    assert "NN" not in TRANCHES and "03" not in TRANCHES
    assert all(lo <= hi for lo, hi in TRANCHES.values())
    assert set(TRANCHE_LIBELLES) == set(TRANCHES)


def test_query_department_filter():
    assert "LIKE '35%'" in build_query(dep="35")
    assert "LIKE" not in build_query()
    with pytest.raises(ValueError):
        build_query(dep="35'; DROP")


# --- Réseau (lit seulement les métadonnées des parquet distants) --------------------------


def test_query_is_valid_sql():
    try:
        con = connect()
        cols = con.sql(f"DESCRIBE {build_query(dep='35')}").df().column_name.tolist()
    except (duckdb.IOException, duckdb.HTTPException) as e:  # pas de réseau
        pytest.skip(f"réseau indisponible : {e}")
    df = pd.DataFrame(columns=cols)
    for c in ("adresse", "nom_etablissement", "diffusion_partielle", "naf_section"):
        assert c in cols
    # les colonnes du contrat absentes de la requête sont ajoutées par enrich()
    check_columns(enrich(df.assign(tranche_effectif=pd.Series(dtype=str))), "entreprises")


# --- Sur le fichier produit, s'il existe ------------------------------------------------


@pytest.mark.skipif(not FILES["entreprises"].exists(), reason="entreprises.parquet absent")
def test_entreprises_file_respects_contract():
    df = pd.read_parquet(FILES["entreprises"])
    check_columns(df, "entreprises")
    assert df.siret.is_unique
