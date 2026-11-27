"""Liste des communes de France pour le suggesteur de ville (T55).

    df = load_communes()            # label, nom, code_postal, code_insee, lat, lon, population
    place = place_of("Rennes (35000)", df)

Source : API Découpage administratif (geo.api.gouv.fr, sans clé), **un seul appel** pour toute
la France, gardé 30 jours dans le cache disque (PATHS.cache). Une ligne par couple
(commune, code postal), libellé « Nom (code postal) », triée par population décroissante pour
que les grandes villes sortent en premier quand on tape. Réseau indisponible : repli sur les
communes du référentiel entreprises (`entreprises.parquet`).
"""

from __future__ import annotations

import logging
from datetime import timedelta

import pandas as pd
import requests
import requests_cache

from radar.config import FILES, PATHS
from radar.geocode import Place

log = logging.getLogger(__name__)

COMMUNES_URL = "https://geo.api.gouv.fr/communes"
COMMUNES_PARAMS = {"fields": "nom,code,codesPostaux,centre,population", "format": "json"}
COLUMNS = ["label", "nom", "code_postal", "code_insee", "lat", "lon", "population"]


def _session() -> requests.Session:
    return requests_cache.CachedSession(
        str(PATHS.cache / "geo_api_communes"), backend="sqlite", expire_after=timedelta(days=30)
    )


def parse_communes(payload: list[dict]) -> pd.DataFrame:
    """Réponse JSON de geo.api.gouv.fr → une ligne par (commune, code postal)."""
    rows = []
    for c in payload:
        centre = (c.get("centre") or {}).get("coordinates")
        if not centre:
            continue
        for cp in c.get("codesPostaux") or []:
            rows.append(
                {
                    "nom": c["nom"],
                    "code_postal": cp,
                    "code_insee": c.get("code"),
                    "lat": float(centre[1]),
                    "lon": float(centre[0]),
                    "population": int(c.get("population") or 0),
                }
            )
    return _finish(pd.DataFrame(rows))


def communes_from_companies(path=None) -> pd.DataFrame:
    """Repli hors ligne : communes du référentiel (centre = moyenne des établissements)."""
    path = path or FILES["entreprises"]
    if not path.exists():
        return pd.DataFrame(columns=COLUMNS)
    cols = ["commune", "code_postal", "lat", "lon"]
    e = pd.read_parquet(path, columns=cols).dropna()
    g = (
        e.groupby(["commune", "code_postal"])
        .agg(lat=("lat", "mean"), lon=("lon", "mean"), population=("lat", "size"))
        .reset_index()
        .rename(columns={"commune": "nom"})
    )
    g["nom"] = g["nom"].str.title()
    return _finish(g.assign(code_insee=None))


def _finish(df: pd.DataFrame) -> pd.DataFrame:
    """Libellé « Nom (CP) » unique, tri par population décroissante."""
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)
    df = df.sort_values(["population", "nom"], ascending=[False, True]).reset_index(drop=True)
    df["label"] = df["nom"] + " (" + df["code_postal"].astype(str) + ")"
    dup = df["label"].duplicated(keep=False)  # homonymes partageant un code postal (rare)
    df.loc[dup, "label"] = df.loc[dup, "label"] + " · " + df.loc[dup, "code_insee"].astype(str)
    return df.drop_duplicates("label")[COLUMNS].reset_index(drop=True)


def load_communes(session: requests.Session | None = None) -> pd.DataFrame:
    """Toutes les communes (geo.api.gouv.fr), ou celles du référentiel si le réseau manque."""
    try:
        r = (session or _session()).get(COMMUNES_URL, params=COMMUNES_PARAMS, timeout=30)
        r.raise_for_status()
        df = parse_communes(r.json())
        if not df.empty:
            return df
    except (requests.RequestException, ValueError, KeyError) as exc:
        log.warning("Liste des communes indisponible (%s) : repli sur le référentiel", exc)
    return communes_from_companies()


def place_of(label: str | None, communes: pd.DataFrame) -> Place | None:
    """Libellé choisi dans la liste → Place (centre de la commune), None si inconnu."""
    if not label:
        return None
    row = communes[communes["label"] == label]
    if row.empty:
        return None
    r = row.iloc[0]
    return Place(lat=float(r["lat"]), lon=float(r["lon"]), label=str(r["label"]), score=1.0)
