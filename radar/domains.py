"""T6 — Domain dictionary (radar/domains.yaml): loading and reference classification rule.

Usage:
    from radar.domains import load_domains, classify
    domains = load_domains()                 # {"data": Domain(...), "informatique": ...}
    classify("Stage - Data Analyst H/F")     # "data"
    classify("Chargé d'études", "M1430")     # "marketing" (ambiguous code, no data keyword)

The rule is documented at the top of domains.yaml. T13 (offer classifier) builds on `classify`
and may add more signals (description, etc.).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import yaml

DOMAINS_FILE = Path(__file__).with_name("domains.yaml")
OTHER = "autre"


@dataclass(frozen=True)
class Domain:
    key: str
    label: str
    rome: dict[str, str]  # code → ROME 4.0 label
    rome_partial: dict[str, str]
    keywords: re.Pattern
    exclusions: re.Pattern | None

    def title_matches(self, title: str | None) -> bool:
        if not title or not self.keywords.search(title):
            return False
        return not (self.exclusions and self.exclusions.search(title))


def _compile(patterns: list[str]) -> re.Pattern | None:
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE) if patterns else None


@cache
def load_domains(path: Path = DOMAINS_FILE) -> dict[str, Domain]:
    """Domains in file order (order matters: the first matching domain wins)."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        key: Domain(
            key=key,
            label=d["libelle"],
            rome=d.get("rome") or {},
            rome_partial=d.get("rome_partiel") or {},
            keywords=_compile(d["mots_cles"]),
            exclusions=_compile(d.get("exclusions") or []),
        )
        for key, d in raw["domaines"].items()
    }


def default_domain(path: Path = DOMAINS_FILE) -> str:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["domaine_par_defaut"]


def _codes(code_rome: str | None) -> list[str]:
    """'M1419,M1405' (La bonne alternance gives several codes) → ['M1419', 'M1405']."""
    if not code_rome or not isinstance(code_rome, str):
        return []
    return [c.strip().upper() for c in code_rome.split(",") if c.strip()]


def classify(title: str | None, code_rome: str | None = None) -> str:
    """Domain key of an offer (or "autre"), from its title and optional ROME code(s)."""
    domains = load_domains().values()
    codes = _codes(code_rome)
    for d in domains:  # 1. ambiguous code confirmed by the title
        if any(c in d.rome_partial for c in codes) and d.title_matches(title):
            return d.key
    for d in domains:  # 2. unambiguous code
        if any(c in d.rome for c in codes):
            return d.key
    for d in domains:  # 3. title only
        if d.title_matches(title):
            return d.key
    return OTHER
