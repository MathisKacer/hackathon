"""Filtre v0 des offres par mots-clés dans le titre, en attendant le classifieur T13.

Sert à la couche 1 de la carte (T39) : on préfère rater quelques offres data plutôt
qu'afficher « Accounting Generalist » à un étudiant en data. Les règles sont volontairement
simples et lisibles ; T13 les remplacera (codes ROME, description, etc.).
"""

from __future__ import annotations

import re

import pandas as pd

from radar.config import PATHS

# Titre d'offre « data » : au moins un de ces motifs (insensible à la casse).
DATA_TITLE_PATTERNS = [
    r"\bdata\b",
    r"\bdonn[ée]es\b",
    r"statisti",
    r"biostat",
    r"[ée]conom[ée]tr",
    r"actuai?r",  # actuaire, actuariat, actuarial
    r"machine learning",
    r"deep learning",
    r"\bml\b",
    r"\bia\b",
    r"\bai\b",
    r"intelligence artificielle",
    r"\bllm\b",
    r"\bnlp\b",
    r"vision par ordinateur|computer vision",
    r"business intelligence",
    r"\bbi\b",
    r"power ?bi",
    r"d[ée]cisionnel",
    r"analyste? (de |d')?(donn|data|quantitati)",
    r"\bquant\b|quantitative",
    r"datavi[sz]",
    r"big data",
    r"\bétudes? (statistiques|quantitatives)",
]
DATA_TITLE_RE = re.compile("|".join(DATA_TITLE_PATTERNS), re.IGNORECASE)

STAGE_RE = re.compile(r"\bstag(e|es|iaire|iaires)\b|\binterns?(hip)?\b|\bpfe\b", re.IGNORECASE)
ALTERNANCE_RE = re.compile(
    r"altern|apprenti|apprentissage|contrat (de )?pro(fessionnalisation)?\b|work[- ]?study",
    re.IGNORECASE,
)

CONTRATS = ("stage", "alternance", "emploi")


def is_data_title(title: str | None) -> bool:
    return bool(title) and DATA_TITLE_RE.search(title) is not None


def contract_from_title(title: str | None) -> str:
    """stage / alternance / emploi, déduit du titre (le champ contrat d'Adzuna est souvent vide)."""
    t = title or ""
    if ALTERNANCE_RE.search(t):
        return "alternance"
    if STAGE_RE.search(t):
        return "stage"
    return "emploi"


def load_raw_offers() -> pd.DataFrame:
    """Concatène toutes les sources de data/raw/offres_raw/*.parquet."""
    files = sorted((PATHS.raw / "offres_raw").glob("*.parquet"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def prepare_offers(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute `is_data`, `contrat`, `age_jours` ; garde les offres géolocalisées."""
    if df.empty:
        return df
    out = df.dropna(subset=["lat", "lon"]).copy()
    out["is_data"] = out["titre"].map(is_data_title)
    out["contrat"] = out["titre"].map(contract_from_title)
    pub = pd.to_datetime(out["date_publication"], utc=True, errors="coerce")
    out["age_jours"] = (pd.Timestamp.now(tz="UTC") - pub).dt.days
    return out
