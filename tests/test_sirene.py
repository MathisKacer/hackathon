"""Tests hors réseau du référentiel SIRENE (T20)."""

import duckdb
import pandas as pd
import pytest

from radar.collect.sirene import NAF_CSV, TRANCHES, build_query
from radar.config import FILES
from radar.schemas import check_columns


def test_naf_table():
    naf = pd.read_csv(NAF_CSV, dtype=str)
    assert len(naf) == 732 and naf.naf.is_unique
    assert naf.set_index("naf").loc["62.01Z", "naf_libelle"] == "Programmation informatique"


def test_tranches_exclude_small_and_unknown():
    assert "NN" not in TRANCHES and "03" not in TRANCHES
    assert all(lo <= hi for _, lo, hi in TRANCHES.values())


def test_query_is_valid_sql():
    # Vérifie la syntaxe et les colonnes produites sans rien télécharger.
    con = duckdb.connect()
    con.sql("INSTALL httpfs; LOAD httpfs;")
    cols = con.sql(f"DESCRIBE {build_query('35')}").df().column_name.tolist()
    check_columns(pd.DataFrame(columns=cols), "entreprises")


@pytest.mark.skipif(not FILES["entreprises"].exists(), reason="entreprises.parquet absent")
def test_entreprises_file_respects_contract():
    df = pd.read_parquet(FILES["entreprises"])
    check_columns(df, "entreprises")
    assert df.siret.is_unique
