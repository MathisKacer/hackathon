"""Collecteur La bonne alternance (API api.apprentissage.beta.gouv.fr), France entière.

Deux jeux de données, tous deux rattachés au SIRET :
- les **offres** d'alternance (LBA + partenaires, dont France Travail) → schéma `offres_raw` ;
- les **recruteurs potentiels** : entreprises sans offre publiée mais susceptibles d'embaucher
  des alternants (= signal direct d'« opportunité cachée »).

Stratégie :
1. `GET /job/v1/export` (2 appels/min) renvoie une URL valable 2 min vers un JSON contenant
   TOUTES les opportunités (mis à jour chaque nuit vers 3 h). Le fichier est conservé dans
   `data/raw/lba/` : on ne le retélécharge pas tant que `lastUpdate` n'a pas changé.
2. Repli si l'export échoue : `GET /job/v1/search` département par département (60 appels/min),
   avec un filtre optionnel sur des codes ROME. Réponses mises en cache (requests-cache).

Le numéro de téléphone (`apply.phone`) n'est jamais conservé.
Usage : voir `scripts/collect_lba.py`.
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Iterable, Iterator
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests
import requests_cache

from radar.config import PATHS, USER_AGENT, settings
from radar.schemas import OFFRES_RAW, SCHEMAS, check_columns

log = logging.getLogger(__name__)

BASE_URL = "https://api.apprentissage.beta.gouv.fr/api"
EXPORT_DIR = PATHS.raw / "lba"
MIN_SECONDS_BETWEEN_SEARCH = 1.1  # ≤ 60 appels/min sur /job/v1/search

# Départements métropolitains + DROM (codes INSEE), pour le repli par recherche.
DEPARTEMENTS = (
    [f"{i:02d}" for i in range(1, 96) if i != 20]
    + ["2A", "2B"]
    + ["971", "972", "973", "974", "976"]
)

# Colonnes propres à LBA, ajoutées après celles du contrat `offres_raw`.
LBA_EXTRA_COLUMNS = [
    "partenaire", "naf", "naf_libelle", "taille", "adresse", "niveau_diplome",
    "nb_postes", "statut", "date_expiration", "date_debut", "duree_mois", "teletravail",
    "delegue_ecole",
]  # fmt: skip
COLUMNS = OFFRES_RAW + LBA_EXTRA_COLUMNS
RECRUTEURS_COLUMNS = SCHEMAS["recruteurs_lba"]

_CP_COMMUNE = re.compile(r"\b(\d{5})\s+([^,\d][^,]*?)\s*$")


class LbaError(RuntimeError):
    """Erreur d'appel à l'API La bonne alternance (le message ne contient jamais le jeton)."""


# --------------------------------------------------------------------------- client HTTP


class LbaClient:
    def __init__(self, session: requests.Session | None = None):
        settings.require("lba_api_token")
        self.session = session or requests_cache.CachedSession(
            str(PATHS.cache / "lba_http"),
            backend="sqlite",
            expire_after=requests_cache.NEVER_EXPIRE,  # instantané (D5)
            allowable_codes=[200],
            match_headers=False,  # le jeton (en-tête) n'entre pas dans la clé de cache
        )
        self.session.headers["User-Agent"] = USER_AGENT
        self.session.headers["Authorization"] = f"Bearer {settings.lba_api_token}"
        self._last_search = 0.0

    def _get(self, path: str, params: dict | None = None, cache: bool = True) -> dict:
        kwargs: dict = {"params": params, "timeout": 60}
        if not cache and isinstance(self.session, requests_cache.CachedSession):
            with self.session.cache_disabled():
                resp = self.session.get(BASE_URL + path, **kwargs)
        else:
            resp = self.session.get(BASE_URL + path, **kwargs)
        if resp.status_code in (401, 403):
            raise LbaError(f"LBA HTTP {resp.status_code} : jeton absent, invalide ou sans droit")
        if resp.status_code in (419, 429):
            raise LbaError(f"LBA HTTP {resp.status_code} : limite de débit atteinte, réessayer")
        if resp.status_code != 200:
            raise LbaError(f"LBA HTTP {resp.status_code} : {resp.text[:200]}")
        return resp.json()

    # ---- export complet

    def download_export(self, dest_dir: Path = EXPORT_DIR, force: bool = False) -> Path:
        """Télécharge l'export complet (JSON) s'il manque sur disque ; renvoie son chemin."""
        meta = self._get("/job/v1/export", cache=False)  # URL signée, valable 2 min
        stamp = re.sub(r"[^0-9T]", "", meta["lastUpdate"])[:15]
        dest = dest_dir / f"export_{stamp}.json"
        if dest.exists() and not force:
            log.info("Export %s déjà présent → pas de téléchargement", dest.name)
            return dest
        dest_dir.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".part")
        log.info("Téléchargement de l'export LBA du %s…", meta["lastUpdate"])
        # URL S3 pré-signée : pas d'en-tête Authorization, pas de cache HTTP.
        with requests.get(meta["url"], stream=True, timeout=600) as r:
            r.raise_for_status()
            with tmp.open("wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    f.write(chunk)
        tmp.replace(dest)
        log.info("Export enregistré : %s (%.1f Mo)", dest, dest.stat().st_size / 1e6)
        return dest

    # ---- recherche (repli)

    def search(self, departement: str | None = None, romes: Iterable[str] | None = None) -> dict:
        params: dict = {}
        if departement:
            params["departements"] = departement
        if romes:
            params["romes"] = ",".join(romes)
        wait = MIN_SECONDS_BETWEEN_SEARCH - (time.monotonic() - self._last_search)
        if wait > 0:
            time.sleep(wait)
        data = self._get("/job/v1/search", params)
        self._last_search = time.monotonic()
        for w in data.get("warnings") or []:
            log.warning("LBA (%s) : %s", departement, w.get("message"))
        return data


# --------------------------------------------------------------------------- normalisation


def _get(d: dict | None, *keys):
    """Accès imbriqué tolérant : _get(r, "workplace", "location", "address")."""
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _lat_lon(workplace: dict | None) -> tuple[float | None, float | None]:
    coords = _get(workplace, "location", "geopoint", "coordinates")  # GeoJSON : [lon, lat]
    if isinstance(coords, list | tuple) and len(coords) >= 2:
        return coords[1], coords[0]
    return None, None


def split_address(address: str | None) -> tuple[str | None, str | None]:
    """« 12 rue X 35000 Rennes » → ("35000", "Rennes")."""
    if not address:
        return None, None
    m = _CP_COMMUNE.search(address.strip())
    return (m.group(1), m.group(2).strip()) if m else (None, None)


def _workplace_fields(w: dict | None) -> dict:
    lat, lon = _lat_lon(w)
    address = _get(w, "location", "address")
    cp, commune = split_address(address)
    return {
        "siret": _get(w, "siret"),
        "nom": _get(w, "name") or _get(w, "brand") or _get(w, "legal_name"),
        "raison_sociale": _get(w, "legal_name"),
        "naf": _get(w, "domain", "naf", "code"),
        "naf_libelle": _get(w, "domain", "naf", "label"),
        "taille": _get(w, "size"),
        "adresse": address,
        "code_postal": cp,
        "commune": commune,
        "lat": lat,
        "lon": lon,
        "site_web": _get(w, "website"),
        "opco": _get(w, "domain", "opco"),
        "idcc": _get(w, "domain", "idcc"),
    }


def job_to_row(r: dict, collected_at: str) -> dict:
    w = _workplace_fields(r.get("workplace"))
    offer = r.get("offer") or {}
    contract = r.get("contract") or {}
    ident = r.get("identifier") or {}
    types = contract.get("type") or []
    return {
        "source": "lba",
        "offre_id": str(ident.get("id") or ident.get("partner_job_id")),
        "date_collecte": collected_at,
        "date_publication": _get(offer, "publication", "creation"),
        "titre": offer.get("title"),
        "description": offer.get("description"),
        "entreprise_nom": w["nom"],
        "commune": w["commune"],
        "code_postal": w["code_postal"],
        "lat": w["lat"],
        "lon": w["lon"],
        "contrat_brut": ", ".join(types) if types else "Apprentissage",  # LBA = alternance
        "code_rome": ",".join(offer.get("rome_codes") or []) or None,
        "url": _get(r, "apply", "url"),
        "siret": w["siret"],
        "partenaire": ident.get("partner_label"),
        "naf": w["naf"],
        "naf_libelle": w["naf_libelle"],
        "taille": w["taille"],
        "adresse": w["adresse"],
        "niveau_diplome": _get(offer, "target_diploma", "european"),
        "nb_postes": offer.get("opening_count"),
        "statut": offer.get("status"),
        "date_expiration": _get(offer, "publication", "expiration"),
        "date_debut": contract.get("start"),
        "duree_mois": contract.get("duration"),
        "teletravail": contract.get("remote"),
        # true → le SIRET est celui de l'ÉCOLE, pas de l'entreprise : à écarter du rapprochement.
        "delegue_ecole": bool(r.get("is_delegated")),
    }


def recruiter_to_row(r: dict, collected_at: str) -> dict:
    w = _workplace_fields(r.get("workplace"))
    return {
        "source": "lba",
        "recruteur_id": str(_get(r, "identifier", "id")),
        "date_collecte": collected_at,
        "siret": w["siret"],
        "nom": w["nom"],
        "raison_sociale": w["raison_sociale"],
        "naf": w["naf"],
        "naf_libelle": w["naf_libelle"],
        "taille": w["taille"],
        "adresse": w["adresse"],
        "code_postal": w["code_postal"],
        "commune": w["commune"],
        "lat": w["lat"],
        "lon": w["lon"],
        "site_web": w["site_web"],
        "opco": w["opco"],
        "idcc": w["idcc"],
        "url": _get(r, "apply", "url"),
    }


def split_items(payload) -> tuple[list[dict], list[dict]]:
    """Sépare offres et recruteurs, quelle que soit la forme du JSON.

    Formes acceptées : {"jobs": [...], "recruiters": [...]} (réponse de /search) ou une liste
    plate d'opportunités (export) — une opportunité sans bloc `offer` est un recruteur.
    """
    if isinstance(payload, dict):
        if "jobs" in payload or "recruiters" in payload:
            return list(payload.get("jobs") or []), list(payload.get("recruiters") or [])
        for key in ("data", "items", "opportunities"):
            if isinstance(payload.get(key), list):
                payload = payload[key]
                break
    if not isinstance(payload, list):
        raise ValueError(f"Format d'export LBA inattendu : {type(payload).__name__}")
    jobs = [x for x in payload if isinstance(x, dict) and x.get("offer")]
    recruiters = [x for x in payload if isinstance(x, dict) and not x.get("offer")]
    return jobs, recruiters


def to_frames(
    jobs: Iterable[dict], recruiters: Iterable[dict], collected_at: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    offres = pd.DataFrame([job_to_row(r, collected_at) for r in jobs], columns=COLUMNS)
    offres = offres.drop_duplicates("offre_id")
    recs = pd.DataFrame(
        [recruiter_to_row(r, collected_at) for r in recruiters], columns=RECRUTEURS_COLUMNS
    )
    recs = recs.drop_duplicates(["recruteur_id", "siret"])
    check_columns(offres, "offres_raw")
    check_columns(recs, "recruteurs_lba")
    return offres, recs


# --------------------------------------------------------------------------- collecte


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def collect_from_export(
    path: Path | None = None, force_download: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Charge l'export complet (le télécharge si besoin) et le normalise."""
    if path is None:
        path = LbaClient().download_export(force=force_download)
    with path.open(encoding="utf-8") as f:
        payload = json.load(f)
    jobs, recruiters = split_items(payload)
    collected_at = datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(timespec="seconds")
    offres, recs = to_frames(jobs, recruiters, collected_at)
    offres.attrs["fichier"] = str(path)
    return offres, recs


def iter_search(
    client: LbaClient, departements: Iterable[str], romes: Iterable[str] | None
) -> Iterator[tuple[str, list[dict], list[dict]]]:
    for dep in departements:
        data = client.search(dep, romes)
        yield dep, list(data.get("jobs") or []), list(data.get("recruiters") or [])


def collect_from_search(
    departements: Iterable[str] | None = None, romes: Iterable[str] | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Repli : recherche département par département (réponses en cache)."""
    client = LbaClient()
    all_jobs: list[dict] = []
    all_recs: list[dict] = []
    status: dict[str, str] = {}
    for dep, jobs, recs in iter_search(client, departements or DEPARTEMENTS, romes):
        all_jobs += jobs
        all_recs += recs
        status[dep] = f"{len(jobs)} offres, {len(recs)} recruteurs"
        log.info("Département %s : %s", dep, status[dep])
    offres, recs_df = to_frames(all_jobs, all_recs, _now())
    offres.attrs["status"] = status
    return offres, recs_df
