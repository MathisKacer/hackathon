"""T23 — Procédures collectives (BODACC) → situation de chaque entreprise (D23).

Source : API ouverte du BODACC (opendatasoft, sans clé), annonces de la famille
« Procédures collectives » des PERIOD_YEARS dernières années, téléchargées en un seul export
parquet (~400 000 annonces, ~45 Mo) puis mises en cache dans data/raw/bodacc_collectives.parquet.

Pour chaque SIREN, on garde le **dernier événement qui change la situation** :
    sauvegarde · redressement · liquidation · plan (plan de sauvegarde ou de redressement
    adopté : l'entreprise poursuit) · fin (procédure terminée sans liquidation : plus d'alerte).
Les autres annonces (état des créances, faillite personnelle du dirigeant…) sont ignorées.
Aucune entreprise n'est supprimée : la pénalité et l'alerte sont appliquées dans la couche
orange (radar/procedures.py).

    raw = download()                       # ou load_raw() si déjà téléchargé
    proc = procedures_by_siren(raw)
    ent = enrich_entreprises(pd.read_parquet(FILES["entreprises"]), proc)
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date, timedelta

import pandas as pd
import requests

from radar.config import PATHS, USER_AGENT

log = logging.getLogger(__name__)

EXPORT_URL = (
    "https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/"
    "annonces-commerciales/exports/parquet"
)
RAW_FILE = PATHS.raw / "bodacc_collectives.parquet"
PERIOD_YEARS = 2  # seules les procédures récentes comptent (D23)

# Situations qui déclenchent une alerte (« fin » n'en déclenche pas).
ALERT_TYPES = ("sauvegarde", "redressement", "liquidation", "plan")

# Nature du jugement → situation. Testées dans l'ordre : la première qui correspond gagne.
# (Les natures exactes ont été relevées sur les annonces de novembre 2026.)
_RULES: list[tuple[str, str | None]] = [
    # Événements sans effet sur la situation de l'entreprise
    (r"état des créances|liste des créances|faillite personnelle|interdiction de gérer", None),
    (r"rectification d'erreur|ordonnance du juge-commissaire", None),
    # Fin de procédure sans liquidation
    (
        r"clôture pour extinction du passif|mettant fin à la procédure|rétractation"
        r"|clôture de la procédure à défaut|clôture de la procédure de sauvegarde",
        "fin",
    ),
    (r"résolution du plan", "liquidation"),  # échec du plan → presque toujours liquidation
    # Liquidation (ouverture, conversion, extension, reprise, clôture pour insuffisance d'actif,
    # plan de cession : l'activité est reprise par un tiers, l'entreprise disparaît)
    (r"liquidation judiciaire|insuffisance d'actif|plan de cession", "liquidation"),
    # Plan adopté : l'entreprise poursuit son activité
    (
        r"plan de (redressement|sauvegarde|continuation)|arrêtant le plan"
        r"|modification du plan|modifiant le plan",
        "plan",
    ),
    (r"sortie de crise", "redressement"),  # procédure simplifiée proche du redressement
    (r"redressement judiciaire", "redressement"),
    (r"sauvegarde", "sauvegarde"),
]
_COMPILED = [(re.compile(p, re.IGNORECASE), t) for p, t in _RULES]


def classify_nature(nature: str | None) -> str | None:
    """« Jugement d'ouverture de liquidation judiciaire » → "liquidation", etc."""
    if not nature:
        return None
    for pattern, kind in _COMPILED:
        if pattern.search(nature):
            return kind
    return None


def download(since: date | None = None, out=RAW_FILE, timeout: int = 600) -> pd.DataFrame:
    """Télécharge les annonces de procédures collectives publiées depuis `since`."""
    since = since or date.today() - timedelta(days=365 * PERIOD_YEARS)
    params = {
        "where": f"familleavis=\"collective\" AND dateparution >= date'{since.isoformat()}'",
        "select": "id,dateparution,typeavis,registre,jugement,url_complete",
    }
    log.info("Téléchargement BODACC depuis %s…", since)
    with requests.get(
        EXPORT_URL, params=params, timeout=timeout, stream=True, headers={"User-Agent": USER_AGENT}
    ) as r:
        r.raise_for_status()
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    tmp.replace(out)
    df = pd.read_parquet(out)
    log.info("%s annonces → %s", f"{len(df):,}", out)
    return df


def load_raw(path=RAW_FILE) -> pd.DataFrame:
    return pd.read_parquet(path)


def _parse_jugement(text: str | None) -> tuple[str | None, str | None]:
    try:
        j = json.loads(text) if text else {}
    except (TypeError, ValueError):
        return None, None
    return j.get("nature"), j.get("date")


def procedures_by_siren(raw: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par SIREN : situation actuelle d'après la dernière annonce qui la change.

    Colonnes : siren, procedure_type, procedure_date, procedure_nature, procedure_url.
    Les avis d'annulation sont ignorés ; un rectificatif compte comme une annonce normale.
    """
    df = raw[raw["typeavis"].fillna("annonce") != "annulation"].copy()
    parsed = df["jugement"].map(_parse_jugement)
    df["procedure_nature"] = parsed.str[0]
    df["procedure_type"] = df["procedure_nature"].map(classify_nature)
    df = df[df["procedure_type"].notna()]
    # Date du jugement si elle est lisible, sinon date de parution
    jug_date = pd.to_datetime(parsed.str[1].reindex(df.index), errors="coerce")
    df["procedure_date"] = jug_date.fillna(pd.to_datetime(df["dateparution"], errors="coerce"))
    # registre = "524509114,524 509 114" : le premier SIREN à 9 chiffres
    df["siren"] = df["registre"].fillna("").str.extract(r"(\d{9})", expand=False)
    df = df.dropna(subset=["siren", "procedure_date"])
    df = df.sort_values(["siren", "procedure_date", "id"])
    last = df.groupby("siren", as_index=False).tail(1)
    return last.rename(columns={"url_complete": "procedure_url"})[
        ["siren", "procedure_type", "procedure_date", "procedure_nature", "procedure_url"]
    ].reset_index(drop=True)


def enrich_entreprises(ent: pd.DataFrame, proc: pd.DataFrame) -> pd.DataFrame:
    """Ajoute la situation BODACC aux établissements (par SIREN) et remplit le contrat.

    `procedure_collective` = procédure en cours ou plan (situation qui déclenche une alerte).
    Les colonnes procedure_* sont remplacées si elles existent déjà (relance idempotente).
    """
    cols = ["procedure_type", "procedure_date", "procedure_nature", "procedure_url"]
    out = ent.drop(columns=[c for c in cols if c in ent.columns]).merge(
        proc[["siren", *cols]], on="siren", how="left"
    )
    out.loc[out["procedure_type"].eq("fin"), cols] = None  # procédure terminée : pas d'alerte
    out["procedure_collective"] = out["procedure_type"].isin(ALERT_TYPES)
    return out
