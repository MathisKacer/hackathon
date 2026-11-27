"""Référentiel entreprises (T20) : établissements SIRENE actifs, ≥ 10 salariés, géolocalisés.

Sources (INSEE, Licence Ouverte, lues à distance par DuckDB sans tout télécharger) :
- StockEtablissement : SIRET, NAF, tranche d'effectif, commune, état, statut de diffusion ;
- Géolocalisation des établissements : latitude / longitude (WGS84) ;
- StockUniteLegale : nom de l'entreprise, catégorie (PME / ETI / GE) ;
- Nomenclature NAF rév. 2 (parquet data.gouv) : libellés, section, division.

Les URLs pointent vers la version mensuelle de novembre 2026 ; les mettre à jour ici
si une nouvelle version est publiée (data.gouv, jeux « Base Sirene » et « Géolocalisation »).

Sortie : data/processed/entreprises.parquet (contrat « entreprises » de radar/schemas.py + extras).
Lancer : uv run python scripts/extract_sirene.py [--dep 35]

Fusion des versions de Mathis et de Celia (D11) : base Mathis ; ajouts Celia = nom des
entrepreneurs individuels, `tranche_libelle`, `adresse`, filtre par département.
"""

from __future__ import annotations

import logging
import time

import duckdb
import pandas as pd

from radar.config import FILES, MIN_TRANCHE_EFFECTIF
from radar.schemas import check_columns

log = logging.getLogger(__name__)

URL_ETABLISSEMENTS = (
    "https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-"
    "siren-siret/20261103-101714/stock-stocketablissement-parquet.parquet"
)
URL_GEOLOC = (
    "https://static.data.gouv.fr/resources/geolocalisation-des-etablissements-du-repertoire-sirene"
    "-pour-les-etudes-statistiques/20261123-064215/"
    "geoloc-geolocalisationetablissement-sirene-pour-etudes-statistiques-parquet.parquet"
)
URL_UNITES_LEGALES = (
    "https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-"
    "siren-siret/20261103-095402/stock-stockunitelegale-parquet.parquet"
)
URL_NAF = "https://static.data.gouv.fr/resources/naf-1/20231123-121750/nafr2.parquet"

# Libellés des tranches, pour l'affichage (fiche entreprise).
TRANCHE_LIBELLES = {
    "11": "10 à 19 salariés",
    "12": "20 à 49 salariés",
    "21": "50 à 99 salariés",
    "22": "100 à 199 salariés",
    "31": "200 à 249 salariés",
    "32": "250 à 499 salariés",
    "41": "500 à 999 salariés",
    "42": "1 000 à 1 999 salariés",
    "51": "2 000 à 4 999 salariés",
    "52": "5 000 à 9 999 salariés",
    "53": "10 000 salariés et plus",
}

# Tranches d'effectif INSEE (≥ 10 salariés) : bornes et valeur centrale (pour l'exposition du
# modèle gamma-Poisson). La borne haute de la dernière tranche est arbitraire.
TRANCHES = {
    "11": (10, 19),
    "12": (20, 49),
    "21": (50, 99),
    "22": (100, 199),
    "31": (200, 249),
    "32": (250, 499),
    "41": (500, 999),
    "42": (1000, 1999),
    "51": (2000, 4999),
    "52": (5000, 9999),
    "53": (10000, 20000),
}

QUERY = """
WITH etab AS (
    SELECT
        siret, siren,
        activitePrincipaleEtablissement AS naf,
        trancheEffectifsEtablissement   AS tranche_effectif,
        TRY_CAST(anneeEffectifsEtablissement AS INTEGER) AS annee_effectif,
        codeCommuneEtablissement        AS code_commune,
        codePostalEtablissement         AS code_postal,
        libelleCommuneEtablissement     AS commune,
        etablissementSiege              AS siege,
        statutDiffusionEtablissement = 'P' AS diffusion_partielle,
        coalesce(enseigne1Etablissement, denominationUsuelleEtablissement) AS nom_etablissement,
        NULLIF(trim(concat_ws(' ', numeroVoieEtablissement, indiceRepetitionEtablissement,
            typeVoieEtablissement, libelleVoieEtablissement)), '') AS adresse
    FROM read_parquet('{etab}')
    WHERE etatAdministratifEtablissement = 'A'
      AND trancheEffectifsEtablissement >= '{min_tranche}'
      AND trancheEffectifsEtablissement <> 'NN'
      AND nomenclatureActivitePrincipaleEtablissement = 'NAFRev2'
      {dep_filter}
),
geo AS (
    SELECT siret, y_latitude AS lat, x_longitude AS lon, qualite_xy
    FROM read_parquet('{geo}')
    WHERE siret IN (SELECT siret FROM etab)
),
ul AS (
    SELECT siren,
           coalesce(
               denominationUniteLegale, denominationUsuelle1UniteLegale,
               -- entrepreneurs individuels : prénom + nom
               NULLIF(trim(concat_ws(' ', coalesce(prenomUsuelUniteLegale, prenom1UniteLegale),
                   coalesce(nomUsageUniteLegale, nomUniteLegale))), '')
           ) AS nom_ul,
           categorieEntreprise AS categorie,
           sigleUniteLegale AS sigle
    FROM read_parquet('{ul}')
    WHERE siren IN (SELECT siren FROM etab)
),
naf AS (
    SELECT NIV5 AS naf, LIB_NIV5 AS naf_libelle,
           NIV1 AS naf_section, LIB_NIV1 AS naf_section_libelle, NIV2 AS naf_division
    FROM read_parquet('{naf}')
)
SELECT
    e.siret, e.siren,
    coalesce(ul.nom_ul, e.nom_etablissement) AS nom,
    e.naf, naf.naf_libelle,
    e.tranche_effectif, ul.categorie, ul.sigle,
    -- RGPD : pas de position pour les établissements à diffusion partielle
    CASE WHEN e.diffusion_partielle THEN NULL ELSE geo.lat END AS lat,
    CASE WHEN e.diffusion_partielle THEN NULL ELSE geo.lon END AS lon,
    CASE WHEN e.diffusion_partielle THEN NULL ELSE e.adresse END AS adresse,
    e.commune,
    e.nom_etablissement, e.annee_effectif, e.code_commune, e.code_postal,
    e.siege, e.diffusion_partielle, geo.qualite_xy,
    naf.naf_section, naf.naf_section_libelle, naf.naf_division
FROM etab e
LEFT JOIN geo USING (siret)
LEFT JOIN ul  USING (siren)
LEFT JOIN naf USING (naf)
"""


def build_query(min_tranche: str = MIN_TRANCHE_EFFECTIF, dep: str | None = None) -> str:
    """Requête DuckDB ; `dep` (ex. "35", "974") restreint à un département pour tester vite."""
    if dep is not None and not dep.isalnum():
        raise ValueError(f"code département invalide : {dep!r}")
    return QUERY.format(
        etab=URL_ETABLISSEMENTS,
        geo=URL_GEOLOC,
        ul=URL_UNITES_LEGALES,
        naf=URL_NAF,
        min_tranche=min_tranche,
        dep_filter=f"AND codeCommuneEtablissement LIKE '{dep}%'" if dep else "",
    )


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.sql("INSTALL httpfs; LOAD httpfs;")
    con.sql("SET http_timeout = 600000; SET http_retries = 5;")
    return con


def extract(min_tranche: str = MIN_TRANCHE_EFFECTIF, dep: str | None = None) -> pd.DataFrame:
    con = connect()
    q = build_query(min_tranche, dep)
    t0 = time.monotonic()
    df = con.sql(q).df()
    log.info("%s établissements extraits en %.0f s", len(df), time.monotonic() - t0)
    return enrich(df)


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Colonnes dérivées + colonnes du contrat pas encore alimentées (T22–T24)."""
    df = df.copy()
    bornes = df["tranche_effectif"].map(TRANCHES)
    df["effectif_min"] = bornes.map(lambda b: b[0] if isinstance(b, tuple) else pd.NA)
    df["effectif_max"] = bornes.map(lambda b: b[1] if isinstance(b, tuple) else pd.NA)
    df["tranche_libelle"] = df["tranche_effectif"].map(TRANCHE_LIBELLES)
    # Valeur centrale géométrique : mieux adaptée qu'une moyenne aux tranches très larges.
    df["effectif_estime"] = (
        (df["effectif_min"].astype("Float64") * df["effectif_max"].astype("Float64")) ** 0.5
    ).round()
    cc = df["code_commune"].fillna("")
    df["departement"] = cc.str[:3].where(cc.str.startswith("97"), cc.str[:2])
    # Alimentées plus tard : finances (T22), BODACC (T23), La Bonne Boîte (T24).
    for col in ("ca_n", "ca_n_1", "lbb_proba"):
        df[col] = pd.Series(pd.NA, index=df.index, dtype="Float64")
    df["procedure_collective"] = pd.Series(pd.NA, index=df.index, dtype="boolean")
    check_columns(df, "entreprises")
    return df


def save(df: pd.DataFrame) -> None:
    FILES["entreprises"].parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(FILES["entreprises"], index=False)
