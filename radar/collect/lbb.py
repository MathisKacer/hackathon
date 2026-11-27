"""T28 — Collecteur La Bonne Boîte v2 (France Travail) : établissements susceptibles d'embaucher.

La Bonne Boîte prédit, pour chaque établissement (SIRET) et chaque métier ROME, un
« potentiel d'embauche » (`hiring_potential`, continu) à partir des déclarations d'embauche
réelles (CDI/CDD). C'est le signal qui remplace le proxy de `c_embauche` (L11, D27).

Stratégie (mesurée le 2026-11-27) :
- tous les codes ROME d'un domaine dans UNE requête (le paramètre `rome` se répète), par
  RÉGION (pas besoin de coordonnées), 100 résultats par page (maximum de l'API) ;
- domaine data : ~1 700 établissements en France → une trentaine d'appels seulement ;
- ≤ 1 requête/s (erreur 429 au-delà de ~2 req/s) ; réponses en cache disque (requests-cache),
  donc une relance ne refait aucun appel déjà fait.

Le champ `email` de l'API est un simple drapeau oui/non : il n'est pas conservé.
Usage : `uv run python scripts/collect_lbb.py`.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

import pandas as pd
import requests
import requests_cache

from radar.config import PATHS, USER_AGENT, settings
from radar.domains import load_domains

log = logging.getLogger(__name__)

URL = "https://api.francetravail.io/partenaire/labonneboite/v2/recherche"
SCOPE = "api_labonneboitev2 search office"
PAGE_SIZE = 100  # maximum autorisé
MIN_SECONDS_BETWEEN_CALLS = 1.1
OUT_FILE = PATHS.raw / "lbb.parquet"

# Libellés de région acceptés par l'API (paramètre `region`).
REGIONS = [
    "Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne", "Centre-Val de Loire",
    "Corse", "Grand Est", "Hauts-de-France", "Île-de-France", "Normandie",
    "Nouvelle-Aquitaine", "Occitanie", "Pays de la Loire", "Provence-Alpes-Côte d'Azur",
    "Guadeloupe", "Martinique", "Guyane", "La Réunion", "Mayotte",
]  # fmt: skip

COLUMNS = [
    "siret", "rome", "domaine", "lbb_potentiel", "lbb_fort_potentiel", "nom", "naf",
    "naf_libelle", "commune", "code_postal", "departement", "region", "lat", "lon",
    "date_collecte",
]  # fmt: skip


class LbbError(RuntimeError):
    """Erreur d'appel à La Bonne Boîte (le message ne contient jamais les identifiants)."""


class LbbClient:
    def __init__(self, session: requests.Session | None = None):
        settings.require("ft_client_id", "ft_client_secret", "ft_token_url")
        self.session = session or requests_cache.CachedSession(
            str(PATHS.cache / "lbb_http"),
            backend="sqlite",
            expire_after=requests_cache.NEVER_EXPIRE,  # instantané (D5)
            allowable_codes=[200],
            match_headers=False,  # le jeton (en-tête) n'entre pas dans la clé de cache
        )
        self.session.headers["User-Agent"] = USER_AGENT
        self._token: str | None = None
        self._last_call = 0.0
        self.real_calls = 0

    def _auth(self) -> None:
        if self._token:
            return
        r = requests.post(
            settings.ft_token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.ft_client_id,
                "client_secret": settings.ft_client_secret,
                "scope": SCOPE,
            },
            timeout=30,
        )
        if r.status_code != 200:
            raise LbbError(f"Jeton France Travail refusé (HTTP {r.status_code}) : vérifier le .env")
        self._token = r.json()["access_token"]
        self.session.headers["Authorization"] = f"Bearer {self._token}"

    def search(self, romes: list[str], region: str, page: int = 1) -> dict:
        params = [("rome", c) for c in romes] + [
            ("region", region),
            ("page", str(page)),
            ("page_size", str(PAGE_SIZE)),
        ]
        if isinstance(self.session, requests_cache.CachedSession):
            cached = self.session.get(URL, params=params, only_if_cached=True)
            if cached.status_code == 200:
                return cached.json()
        self._auth()
        wait = MIN_SECONDS_BETWEEN_CALLS - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        resp = self.session.get(URL, params=params, timeout=60)
        self._last_call = time.monotonic()
        self.real_calls += 1
        if resp.status_code == 429:
            raise LbbError("La Bonne Boîte : limite de débit atteinte (429), réessayer plus tard")
        if resp.status_code != 200:
            raise LbbError(f"La Bonne Boîte HTTP {resp.status_code} : {resp.text[:200]}")
        return resp.json()


def item_to_row(item: dict, domain: str, collected_at: str) -> dict:
    loc = item.get("location") or {}
    naf = item.get("naf") or ""
    # L'API renvoie « 6202A » ; SIRENE et le reste du projet utilisent « 62.02A ».
    naf = f"{naf[:2]}.{naf[2:]}" if len(naf) == 5 and "." not in naf else (naf or None)
    return {
        "siret": item.get("siret"),
        "rome": item.get("rome"),
        "domaine": domain,
        "lbb_potentiel": item.get("hiring_potential"),
        "lbb_fort_potentiel": bool(item.get("is_high_potential")),
        "nom": item.get("company_name"),
        "naf": naf,
        "naf_libelle": item.get("naf_label"),
        "commune": item.get("city"),
        "code_postal": item.get("postcode"),
        "departement": item.get("department_number"),
        "region": item.get("region"),
        "lat": loc.get("lat"),
        "lon": loc.get("lon"),
        "date_collecte": collected_at,
    }


def collect(domain: str = "data", client: LbbClient | None = None) -> pd.DataFrame:
    """Tous les établissements La Bonne Boîte pour les codes ROME (non ambigus) du domaine."""
    client = client or LbbClient()
    romes = list(load_domains()[domain].rome)
    collected_at = datetime.now(UTC).isoformat(timespec="seconds")
    rows: list[dict] = []
    for region in REGIONS:
        page = 1
        while True:
            data = client.search(romes, region, page)
            items = data.get("items") or []
            rows += [item_to_row(it, domain, collected_at) for it in items]
            hits = data.get("hits") or 0
            if page == 1:
                log.info("%s : %d établissements × métiers", region, hits)
            if len(items) < PAGE_SIZE or page * PAGE_SIZE >= hits:
                break
            page += 1
    df = pd.DataFrame(rows, columns=COLUMNS)
    df = df.dropna(subset=["siret"]).drop_duplicates(["siret", "rome"])
    log.info("%d appels réels (le reste venait du cache)", client.real_calls)
    return df.reset_index(drop=True)


def best_by_siret(lbb: pd.DataFrame, domain: str) -> pd.DataFrame:
    """Un établissement peut sortir pour plusieurs métiers du domaine : on garde le maximum."""
    d = lbb[lbb["domaine"] == domain]
    return (
        d.groupby("siret")
        .agg(
            lbb_potentiel=("lbb_potentiel", "max"), lbb_fort_potentiel=("lbb_fort_potentiel", "any")
        )
        .reset_index()
    )
