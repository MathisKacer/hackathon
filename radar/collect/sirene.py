"""T20 — Référentiel SIRENE France → data/processed/entreprises.parquet.

Lit les trois stocks parquet SIRENE (data.gouv) *à distance* avec DuckDB (httpfs),
sans télécharger les 3,7 Go : seules les colonnes utiles sont lues.

Filtre : établissements actifs, >= 10 salariés (tranches INSEE '11' à '53').
Résultat : ~400 k établissements, une ligne par SIRET, au schéma de
docs/ARCHITECTURE.md (colonnes `entreprises.parquet`).

Lancer :
    uv run python -m radar.collect.sirene            # France entière
    uv run python -m radar.collect.sirene --dep 35   # un département (test rapide)
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import duckdb

from radar.config import FILES

# Stocks SIRENE de novembre 2026 (mettre à jour les URL au prochain millésime).
URL_ETABLISSEMENTS = (
    "https://static.data.gouv.fr/resources/"
    "base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/"
    "20261103-101714/stock-stocketablissement-parquet.parquet"
)
URL_UNITES_LEGALES = (
    "https://static.data.gouv.fr/resources/"
    "base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/"
    "20261103-095402/stock-stockunitelegale-parquet.parquet"
)
URL_GEOLOC = (
    "https://static.data.gouv.fr/resources/"
    "geolocalisation-des-etablissements-du-repertoire-sirene-pour-les-etudes-statistiques/"
    "20261123-064215/"
    "geoloc-geolocalisationetablissement-sirene-pour-etudes-statistiques-parquet.parquet"
)

# Libellés NAF rév. 2 (INSEE, naf2008_liste_n5.xls converti en CSV, 732 sous-classes)
NAF_CSV = Path(__file__).resolve().parent.parent / "naf_rev2.csv"

# Tranches d'effectif INSEE -> (libellé, min, max). 'NN', '00'..'03' sont exclues.
TRANCHES = {
    "11": ("10 à 19 salariés", 10, 19),
    "12": ("20 à 49 salariés", 20, 49),
    "21": ("50 à 99 salariés", 50, 99),
    "22": ("100 à 199 salariés", 100, 199),
    "31": ("200 à 249 salariés", 200, 249),
    "32": ("250 à 499 salariés", 250, 499),
    "41": ("500 à 999 salariés", 500, 999),
    "42": ("1 000 à 1 999 salariés", 1000, 1999),
    "51": ("2 000 à 4 999 salariés", 2000, 4999),
    "52": ("5 000 à 9 999 salariés", 5000, 9999),
    "53": ("10 000 salariés et plus", 10000, 20000),
}


def _tranches_sql() -> str:
    rows = ", ".join(f"('{code}', '{lib}', {lo}, {hi})" for code, (lib, lo, hi) in TRANCHES.items())
    return f"SELECT * FROM (VALUES {rows}) t(code, libelle, effectif_min, effectif_max)"


def build_query(dep: str | None = None) -> str:
    """Requête DuckDB qui produit entreprises.parquet (une ligne par SIRET)."""
    dep_filter = f"AND e.codeCommuneEtablissement LIKE '{dep}%'" if dep else ""
    return f"""
    WITH tranches AS ({_tranches_sql()}),
    naf AS (SELECT * FROM read_csv('{NAF_CSV}', header = true, all_varchar = true)),
    etab AS (
        SELECT
            e.siret, e.siren,
            e.activitePrincipaleEtablissement            AS naf,
            e.trancheEffectifsEtablissement              AS tranche_effectif,
            e.anneeEffectifsEtablissement                AS annee_effectifs,
            e.statutDiffusionEtablissement = 'O'         AS diffusible,
            e.etablissementSiege                         AS siege,
            e.codePostalEtablissement                    AS code_postal,
            e.codeCommuneEtablissement                   AS code_commune,
            e.libelleCommuneEtablissement                AS commune,
            NULLIF(trim(concat_ws(' ', e.numeroVoieEtablissement, e.indiceRepetitionEtablissement,
                e.typeVoieEtablissement, e.libelleVoieEtablissement)), '') AS adresse,
            COALESCE(e.denominationUsuelleEtablissement, e.enseigne1Etablissement) AS nom_etab
        FROM read_parquet('{URL_ETABLISSEMENTS}') e
        WHERE e.etatAdministratifEtablissement = 'A'
          AND e.trancheEffectifsEtablissement IN (SELECT code FROM tranches)
          AND e.nomenclatureActivitePrincipaleEtablissement = 'NAFRev2'
          {dep_filter}
    ),
    ul AS (
        SELECT
            siren,
            COALESCE(
                denominationUniteLegale,
                NULLIF(trim(concat_ws(' ', COALESCE(prenomUsuelUniteLegale, prenom1UniteLegale),
                    COALESCE(nomUsageUniteLegale, nomUniteLegale))), '')
            ) AS nom_ul,
            sigleUniteLegale     AS sigle,
            categorieEntreprise  AS categorie
        FROM read_parquet('{URL_UNITES_LEGALES}')
        WHERE siren IN (SELECT siren FROM etab)
    ),
    geo AS (
        SELECT siret, y_latitude AS lat, x_longitude AS lon, qualite_xy
        FROM read_parquet('{URL_GEOLOC}')
        WHERE siret IN (SELECT siret FROM etab)
    )
    SELECT
        etab.siret, etab.siren,
        COALESCE(etab.nom_etab, ul.nom_ul, ul.sigle)  AS nom,
        ul.nom_ul                                     AS nom_entreprise,
        ul.sigle,
        etab.naf,
        naf.naf_libelle,
        etab.tranche_effectif,
        t.libelle                                     AS tranche_libelle,
        t.effectif_min, t.effectif_max,
        etab.annee_effectifs,
        ul.categorie,
        etab.siege,
        geo.lat, geo.lon, geo.qualite_xy,
        etab.commune, etab.code_postal, etab.code_commune,
        CASE WHEN etab.code_commune LIKE '97%' THEN left(etab.code_commune, 3)
             ELSE left(etab.code_commune, 2) END      AS departement,
        CASE WHEN etab.diffusible THEN etab.adresse END AS adresse,
        etab.diffusible,
        -- Colonnes du contrat remplies par d'autres tâches (T22, T23, T24)
        CAST(NULL AS DOUBLE)                          AS ca_n,
        CAST(NULL AS DOUBLE)                          AS ca_n_1,
        FALSE                                         AS procedure_collective,
        CAST(NULL AS DOUBLE)                          AS lbb_proba
    FROM etab
    JOIN tranches t ON t.code = etab.tranche_effectif
    LEFT JOIN ul  USING (siren)
    LEFT JOIN geo USING (siret)
    LEFT JOIN naf ON naf.naf = etab.naf
    ORDER BY etab.siret
    """


def extract(dep: str | None = None, out: Path | str | None = None) -> Path:
    """Écrit le référentiel en parquet et renvoie son chemin."""
    out = Path(out or FILES["entreprises"])
    with duckdb.connect() as con:
        con.sql("INSTALL httpfs; LOAD httpfs; SET enable_progress_bar = false;")
        t0 = time.time()
        con.sql(f"COPY ({build_query(dep)}) TO '{out}' (FORMAT parquet, COMPRESSION zstd)")
        n, n_geo, n_siren, pct_sans_nom = con.sql(
            f"""SELECT count(*), count(lat), count(DISTINCT siren),
                       round(100 * avg(CASE WHEN nom IS NULL THEN 1 ELSE 0 END), 2)
                FROM read_parquet('{out}')"""
        ).fetchall()[0]
    print(
        f"{out} : {n:,} établissements, {n_geo:,} géolocalisés, "
        f"{n_siren:,} entreprises, {pct_sans_nom} % sans nom ({time.time() - t0:.0f} s)"
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dep", help="code département (ex. 35) pour un test rapide")
    args = parser.parse_args()
    extract(args.dep)


if __name__ == "__main__":
    main()
