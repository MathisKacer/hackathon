"""Collecteur Adzuna (offres d'emploi agrégées, France).

Contraintes :
- quota gratuit ~250 appels/jour et ~25/min → chaque appel réel est compté dans
  `data/cache/adzuna_quota.json` et la collecte s'arrête avant la limite ;
- toutes les réponses sont mises en cache (requests-cache, SQLite) : relancer la collecte ne
  consomme du quota que pour les pages pas encore téléchargées. Les clés ne sont pas stockées
  dans le cache (paramètres ignorés).

Usage : voir `scripts/collect_adzuna.py`.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime

import pandas as pd
import requests_cache

from radar.config import PATHS, USER_AGENT, settings
from radar.schemas import OFFRES_RAW, check_columns

log = logging.getLogger(__name__)

BASE_URL = "https://api.adzuna.com/v1/api/jobs/fr/search/{page}"
RESULTS_PER_PAGE = 50  # maximum autorisé par Adzuna
MIN_SECONDS_BETWEEN_CALLS = 2.6  # ≤ 25 appels/min
DEFAULT_DAILY_LIMIT = 240  # marge sous les ~250/jour

# Régions dans l'ordre de priorité de la collecte (libellés Adzuna, niveau location1).
REGIONS = [
    "Bretagne",
    "Ile-de-France",
    "Pays de la Loire",
    "Auvergne-Rhône-Alpes",
    "Occitanie",
    "Nouvelle-Aquitaine",
    "Hauts-de-France",
    "Provence-Alpes-Côte d'Azur",
    "Grand Est",
    "Normandie",
    "Centre-Val de Loire",
    "Bourgogne-Franche-Comté",
    "Corse",
]

# Colonnes du contrat `offres_raw` (docs/ARCHITECTURE.md) + colonnes propres à Adzuna.
ADZUNA_EXTRA_COLUMNS = [
    "contrat_temps", "categorie", "salaire_min", "salaire_max", "salaire_predit",
    "zone", "requete", "region_requete",
]  # fmt: skip
COLUMNS = OFFRES_RAW + ADZUNA_EXTRA_COLUMNS


class QuotaExceeded(RuntimeError):
    """Le quota journalier (local) est atteint ou Adzuna a répondu 429."""


@dataclass
class Quota:
    """Compteur d'appels réels (hors cache) par jour UTC, persistant sur disque."""

    daily_limit: int = DEFAULT_DAILY_LIMIT
    path = PATHS.cache / "adzuna_quota.json"

    def _load(self) -> dict[str, int]:
        if self.path.exists():
            return json.loads(self.path.read_text())
        return {}

    @staticmethod
    def _today() -> str:
        return datetime.now(UTC).strftime("%Y-%m-%d")

    @property
    def used_today(self) -> int:
        return self._load().get(self._today(), 0)

    @property
    def remaining(self) -> int:
        return max(self.daily_limit - self.used_today, 0)

    def record(self) -> None:
        data = self._load()
        data[self._today()] = data.get(self._today(), 0) + 1
        self.path.write_text(json.dumps(data, indent=1))


class AdzunaClient:
    def __init__(self, daily_limit: int = DEFAULT_DAILY_LIMIT, max_calls: int | None = None):
        settings.require("adzuna_app_id", "adzuna_app_key")
        self.session = requests_cache.CachedSession(
            str(PATHS.cache / "adzuna_http"),
            backend="sqlite",
            expire_after=requests_cache.NEVER_EXPIRE,  # instantané : on ne rafraîchit pas
            ignored_parameters=["app_id", "app_key"],  # clés hors du cache
            allowable_codes=[200],
        )
        self.session.headers["User-Agent"] = USER_AGENT
        self.quota = Quota(daily_limit)
        self.max_calls = max_calls  # plafond pour cette exécution (en plus du quota du jour)
        self.real_calls = 0
        self._last_call = 0.0

    def _get(self, page: int, params: dict) -> dict:
        url = BASE_URL.format(page=page)
        full = {
            "app_id": settings.adzuna_app_id,
            "app_key": settings.adzuna_app_key,
            "results_per_page": RESULTS_PER_PAGE,
            "content-type": "application/json",
            **params,
        }
        # Réponse déjà en cache → aucun appel réseau, aucun quota consommé.
        cached = self.session.get(url, params=full, only_if_cached=True)
        if cached.status_code == 200:
            return cached.json()

        if self.quota.remaining <= 0:
            raise QuotaExceeded(f"Quota local du jour atteint ({self.quota.used_today} appels)")
        if self.max_calls is not None and self.real_calls >= self.max_calls:
            raise QuotaExceeded(f"Plafond de cette exécution atteint ({self.max_calls} appels)")

        wait = MIN_SECONDS_BETWEEN_CALLS - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        resp = self.session.get(url, params=full, timeout=30)
        self._last_call = time.monotonic()
        self.quota.record()
        self.real_calls += 1
        if resp.status_code == 429:
            raise QuotaExceeded("Adzuna a répondu 429 (trop de requêtes)")
        if resp.status_code != 200:
            raise RuntimeError(f"Adzuna HTTP {resp.status_code} : {resp.text[:200]}")
        return resp.json()

    def iter_search(
        self, what: str, region: str | None = None, max_days_old: int = 60, max_pages: int = 100
    ) -> Iterator[tuple[int, list[dict]]]:
        """Itère sur les pages de résultats : (count total, résultats de la page)."""
        params: dict = {"what": what, "max_days_old": max_days_old, "sort_by": "date"}
        if region:
            params |= {"location0": "France", "location1": region}
        for page in range(1, max_pages + 1):
            data = self._get(page, params)
            results = data.get("results", [])
            yield data.get("count", 0), results
            if len(results) < RESULTS_PER_PAGE or page * RESULTS_PER_PAGE >= data.get("count", 0):
                return


def _to_row(r: dict, what: str, region: str | None, collected_at: str) -> dict:
    loc = r.get("location") or {}
    area = loc.get("area") or []
    return {
        "source": "adzuna",
        "offre_id": str(r.get("id")),
        "date_collecte": collected_at,
        "date_publication": r.get("created"),
        "titre": r.get("title"),
        "description": r.get("description"),  # tronquée (~500 caractères) par Adzuna
        "entreprise_nom": (r.get("company") or {}).get("display_name"),
        "commune": area[-1] if len(area) >= 3 else loc.get("display_name"),
        "code_postal": None,
        "lat": r.get("latitude"),
        "lon": r.get("longitude"),
        "contrat_brut": r.get("contract_type"),  # souvent vide → déduire du texte (T13)
        "code_rome": None,
        "url": r.get("redirect_url"),
        "siret": None,  # Adzuna ne fournit pas de SIRET → rapprochement (T21)
        "contrat_temps": r.get("contract_time"),
        "categorie": (r.get("category") or {}).get("label"),
        "salaire_min": r.get("salary_min"),
        "salaire_max": r.get("salary_max"),
        "salaire_predit": r.get("salary_is_predicted") == "1",
        "zone": " > ".join(area),
        "requete": what,
        "region_requete": region,
    }


def collect(
    what: str = "data",
    regions: list[str] | None = None,
    max_days_old: int = 60,
    daily_limit: int = DEFAULT_DAILY_LIMIT,
    max_calls: int | None = None,
) -> pd.DataFrame:
    """Collecte les offres région par région jusqu'à épuisement du quota.

    S'arrête proprement sur QuotaExceeded : tout ce qui a été téléchargé est en cache et
    sera réutilisé gratuitement à la prochaine exécution, qui reprendra là où on s'est arrêté.
    """
    client = AdzunaClient(daily_limit=daily_limit, max_calls=max_calls)
    collected_at = datetime.now(UTC).isoformat(timespec="seconds")
    rows: list[dict] = []
    status: dict[str, str] = {}
    for region in regions or REGIONS:
        n_before, total = len(rows), 0
        try:
            for page_count, results in client.iter_search(what, region, max_days_old):
                total = page_count
                rows.extend(_to_row(r, what, region, collected_at) for r in results)
            got = len(rows) - n_before
            # Plafond de pages atteint avant la fin → région incomplète (à découper par département)
            label = "complet" if got >= total else "tronqué (plafond de pages)"
            status[region] = f"{label} ({got}/{total})"
        except QuotaExceeded as e:
            status[region] = f"partiel ({len(rows) - n_before} offres) — {e}"
            log.warning("Arrêt : %s", e)
            break
        log.info("%s : %s", region, status[region])
    for region in regions or REGIONS:
        status.setdefault(region, "non commencé")

    df = pd.DataFrame(rows, columns=COLUMNS).drop_duplicates("offre_id")
    check_columns(df, "offres_raw")
    df.attrs["status"] = status
    df.attrs["real_calls"] = client.real_calls
    df.attrs["quota_used_today"] = client.quota.used_today
    return df
