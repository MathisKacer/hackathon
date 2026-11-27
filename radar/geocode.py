"""Géocodage d'une adresse (T40) via l'API Géoplateforme de l'IGN (BAN), sans clé.

    from radar.geocode import geocode
    geocode("51 rue Blaise Pascal, Bruz")  # → Place(lat=48.05…, lon=-1.74…, label="51 Rue…")

Les réponses sont gardées dans un cache disque (PATHS.cache) : une adresse déjà cherchée ne
refait pas d'appel, et la démo marche hors ligne pour les adresses déjà essayées.
En cas d'échec réseau ou d'adresse introuvable, renvoie None (l'app affiche un message).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

import requests
import requests_cache

from radar.config import PATHS

log = logging.getLogger(__name__)

GEOCODE_URL = "https://data.geopf.fr/geocodage/search"
_session: requests.Session | None = None


@dataclass(frozen=True)
class Place:
    lat: float
    lon: float
    label: str
    score: float  # confiance renvoyée par la BAN, dans [0, 1]


def _get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests_cache.CachedSession(
            str(PATHS.cache / "geoplateforme"),
            backend="sqlite",
            expire_after=timedelta(days=30),
        )
    return _session


def parse_response(payload: dict) -> Place | None:
    """Premier résultat d'une réponse GeoJSON de la Géoplateforme, ou None."""
    features = payload.get("features") or []
    if not features:
        return None
    f = features[0]
    lon, lat = f["geometry"]["coordinates"][:2]
    props = f.get("properties", {})
    return Place(
        lat=float(lat),
        lon=float(lon),
        label=str(props.get("label", "")),
        score=float(props.get("score", 0.0)),
    )


def geocode(address: str, session: requests.Session | None = None) -> Place | None:
    """Adresse (ou ville, code postal…) → Place ; None si vide, introuvable ou réseau en panne."""
    address = (address or "").strip()
    if len(address) < 3:
        return None
    s = session or _get_session()
    try:
        r = s.get(GEOCODE_URL, params={"q": address, "limit": 1}, timeout=10)
        r.raise_for_status()
        return parse_response(r.json())
    except (requests.RequestException, ValueError, KeyError) as exc:
        log.warning("Géocodage impossible pour %r : %s", address, exc)
        return None
