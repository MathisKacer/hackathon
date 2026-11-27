"""T13 — Offer classifier: raw offers (data/raw/offres_raw/*.parquet) → offres.parquet.

For each offer:
- `domaine`  : radar.domains.classify(title, ROME code) → key of domains.yaml or "autre";
- `contrat`  : stage / alternance / emploi (rules below);
- `domaine_regle`, `contrat_regle` : which rule decided (to explain and audit the result);
- `siret_match, match_score, match_methode` : only what the SOURCE already gives
  (La bonne alternance). Name + town matching for Adzuna is T21 (@mathis), which fills in
  the rows left with match_methode = "a_rapprocher".

Contract rules (first that applies):
1. raw contract says apprenticeship ("Apprentissage", "Professionnalisation", LBA) → alternance;
2. title mentions alternance / apprentice / contrat pro                             → alternance;
3. title mentions stage / stagiaire / internship / PFE / trainee                    → stage;
4. otherwise                                                                         → emploi.
The title wins over Adzuna's `contract_type`, which is rarely filled and only says
permanent/contract. "Stage ou alternance" → alternance (rule 2 comes first).

Usage: `uv run python scripts/classify_offres.py`.
"""

from __future__ import annotations

import re

import pandas as pd

from radar.config import PATHS
from radar.domains import classify_with_rule
from radar.schemas import check_columns

RAW_DIR = PATHS.raw / "offres_raw"

# Same spirit as radar/process/quick_filter.py (T39), plus "trainee" and "alternant(e)".
ALTERNANCE_RE = re.compile(
    r"altern|apprenti|apprentissage|contrat (de )?pro(fessionnalisation)?\b|work[- ]?study",
    re.IGNORECASE,
)
STAGE_RE = re.compile(
    r"\bstag(e|es|iaire|iaires)\b|\binterns?(hip)?\b|\bpfe\b|\btrainee\b", re.IGNORECASE
)
APPRENTICESHIP_RAW_RE = re.compile(r"apprentissage|professionnalisation", re.IGNORECASE)

# Values of `match_methode` written here (T21 adds its own, e.g. "nom_commune_fuzzy").
MATCH_FROM_SOURCE = "siret_source"
MATCH_SCHOOL = "siret_ecole_exclu"  # LBA offer delegated to a school: SIRET is the school's
MATCH_TODO = "a_rapprocher"  # no SIRET from the source → T21


def contract_with_rule(title: str | None, contrat_brut: str | None) -> tuple[str, str]:
    if isinstance(contrat_brut, str) and APPRENTICESHIP_RAW_RE.search(contrat_brut):
        return "alternance", "contrat_brut"
    t = title if isinstance(title, str) else ""
    if ALTERNANCE_RE.search(t):
        return "alternance", "titre"
    if STAGE_RE.search(t):
        return "stage", "titre"
    return "emploi", "defaut"


def load_raw_offers(raw_dir=RAW_DIR) -> pd.DataFrame:
    """All sources of data/raw/offres_raw/*.parquet, stacked (source-specific columns kept)."""
    files = sorted(raw_dir.glob("*.parquet"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def classify_offers(raw: pd.DataFrame) -> pd.DataFrame:
    """Add domain, contract and source-given SIRET columns (contract of offres.parquet)."""
    check_columns(raw, "offres_raw")
    out = raw.drop_duplicates(["source", "offre_id"]).reset_index(drop=True)

    # Classify each distinct (title, ROME) pair once: many offers share the same title.
    keys = out[["titre", "code_rome"]].astype("string").fillna("")
    uniq = keys.drop_duplicates()
    dom = {
        (t, c): classify_with_rule(t or None, c or None) for t, c in uniq.itertuples(index=False)
    }
    res = [dom[k] for k in keys.itertuples(index=False, name=None)]
    out["domaine"] = [r[0] for r in res]
    out["domaine_regle"] = [r[1] for r in res]

    ctr = [contract_with_rule(t, b) for t, b in zip(out["titre"], out["contrat_brut"], strict=True)]
    out["contrat"] = [r[0] for r in ctr]
    out["contrat_regle"] = [r[1] for r in ctr]

    delegated = (
        out["delegue_ecole"].fillna(False).astype(bool)
        if "delegue_ecole" in out
        else pd.Series(False, index=out.index)
    )
    has_siret = out["siret"].notna() & (out["siret"].astype("string").str.len() > 0)
    from_source = has_siret & ~delegated
    out["siret_match"] = out["siret"].where(from_source)
    out["match_score"] = pd.Series(100.0, index=out.index).where(from_source)
    out["match_methode"] = MATCH_TODO
    out.loc[from_source, "match_methode"] = MATCH_FROM_SOURCE
    out.loc[has_siret & delegated, "match_methode"] = MATCH_SCHOOL

    check_columns(out, "offres")
    return out


def summary(offres: pd.DataFrame, top_other: int = 15) -> str:
    """Text report: domain × contract counts, rules used, most frequent unclassified titles."""
    lines = [f"{len(offres):,} offres".replace(",", " ")]
    tab = pd.crosstab(offres["domaine"], offres["contrat"], margins=True, margins_name="total")
    lines += ["", "Domaine × contrat :", tab.to_string()]
    lines += ["", "Règle de domaine :", offres["domaine_regle"].value_counts().to_string()]
    lines += ["", "Règle de contrat :", offres["contrat_regle"].value_counts().to_string()]
    lines += ["", "SIRET :", offres["match_methode"].value_counts().to_string()]
    other = offres.loc[offres["domaine"] == "autre", "titre"].value_counts().head(top_other)
    if len(other):
        lines += ["", "Titres « autre » les plus fréquents (pour T8) :", other.to_string()]
    return "\n".join(lines)
