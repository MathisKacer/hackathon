"""T67 — Niveau d'études attendu d'une offre.

Deux sources (D33) :
- La bonne alternance donne le diplôme visé (`niveau_diplome` = `target_diploma.european`) ;
- Adzuna ne le donne pas : on le cherche dans le titre et la description (tronquée à ~500
  caractères par Adzuna) avec des expressions simples (« Bac+5 », « Master », « M2 »…).

Niveaux du cadre européen des certifications, comme LBA : "3" CAP, "4" Bac, "5" Bac+2,
"6" Bac+3/4, "7" Bac+5, "8" Doctorat. Une offre peut en citer plusieurs (« Bac+3 à Bac+5 ») :
`niveaux_etudes` est la liste triée, en texte « 6,7 » (facile à stocker), None si rien.

    detect_levels("Stage Data Analyst - Bac+5", "Master 2 en statistiques")   # ["7"]
    offer_levels(row)                                                         # "6,7" ou None
    levels_label("6,7")                                                       # "Bac+3/4 à Bac+5"
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

LEVELS = ["3", "4", "5", "6", "7", "8"]
LEVEL_LABELS = {
    "3": "CAP",
    "4": "Bac",
    "5": "Bac+2",
    "6": "Bac+3/4",
    "7": "Bac+5",
    "8": "Doctorat",
}
UNKNOWN = "Non précisé"

# « bac+5 », « bac +3 », « bac + 2 », « bac+3/4 », « bac+4/5 » : chiffre(s) après le plus.
_BAC_PLUS = re.compile(r"\bbac\s*\+?\s*(\d)(?:\s*[/a-]\s*(?:bac\s*\+?\s*)?(\d))?\b")
_BAC_PLUS_LEVEL = {"1": "4", "2": "5", "3": "6", "4": "6", "5": "7", "6": "7", "8": "8"}
# Mots-clés → niveau (sur un texte en minuscules, sans accents). Choix prudents : pas « BUT »
# (le mot « but »), pas « CAP » (Cap Gemini…), pas « ingénieur » seul (c'est souvent le métier),
# et « master » sauf « Master Data », « Scrum Master »… (métiers, fréquents dans le domaine data).
_MASTER = (
    r"(?<!scrum )(?<!data )(?<!annee de )\bmasters?\b"
    r"(?!\s*(data|donnees?|class|planning|file|record|plan|gestion|chef)\b)"
    r"(?!\s*(de|des|du)\s*(la\s*)?(donnee|data|production|planning)s?\b)"
)
_KEYWORDS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(doctorat|phd|ph\.d|doctoral|doctorant|these cifre|cifre)\b"), "8"),
    (re.compile(_MASTER + r"(?!\s*(1|i)\b)"), "7"),
    (re.compile(r"\b(mastere|msc|m2)\b"), "7"),
    (
        re.compile(
            r"\b(ecole d'ingenieurs?|ecole d.ingenieur|diplome d'ingenieur|cycle ingenieur)\b"
        ),
        "7",
    ),  # noqa: E501
    (re.compile(r"\b(grande ecole|ecole de commerce|business school)\b"), "7"),
    (re.compile(r"\b(m1|master\s*(1|i)|premiere annee de master)\b"), "6"),
    (re.compile(r"\b(licence|bachelor|licence pro(fessionnelle)?)\b"), "6"),
    (re.compile(r"\b(bts|dut|deust)\b"), "5"),
    (re.compile(r"\bniveau bac\b(?!\s*\+)"), "4"),
]


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.replace("’", "'")


def detect_levels(*texts: str | None) -> list[str]:
    """Niveaux cités dans des textes libres (titre, description), triés ; [] si aucun."""
    text = _normalize(" ".join(t for t in texts if isinstance(t, str)))
    if not text:
        return []
    found: set[str] = set()
    for m in _BAC_PLUS.finditer(text):
        for digit in m.groups():
            if digit in _BAC_PLUS_LEVEL:
                found.add(_BAC_PLUS_LEVEL[digit])
    for pattern, level in _KEYWORDS:
        if pattern.search(text):
            found.add(level)
    return sorted(found)


def offer_levels(row: pd.Series | dict) -> str | None:
    """Niveaux d'une offre en texte « 6,7 » : champ de la source s'il existe, sinon le texte."""
    get = row.get
    given = get("niveau_diplome")
    if isinstance(given, str) and given.strip() in LEVEL_LABELS:
        return given.strip()
    found = detect_levels(get("titre"), get("description"))
    return ",".join(found) or None


def add_levels(offers: pd.DataFrame) -> pd.DataFrame:
    """Ajoute `niveaux_etudes` (« 6,7 » ou None) à un tableau d'offres."""
    if offers.empty:
        return offers.assign(niveaux_etudes=pd.Series(dtype=object))
    cols = [c for c in ("titre", "description", "niveau_diplome") if c in offers]
    levels = [offer_levels(r) for r in offers[cols].to_dict("records")]
    return offers.assign(niveaux_etudes=pd.Series(levels, index=offers.index, dtype=object))


def levels_label(levels: str | None) -> str:
    """« 6,7 » → « Bac+3/4 à Bac+5 » ; « 7 » → « Bac+5 » ; None → « Non précisé »."""
    if not isinstance(levels, str) or not levels:
        return UNKNOWN
    codes = [c for c in levels.split(",") if c in LEVEL_LABELS]
    if not codes:
        return UNKNOWN
    lo, hi = LEVEL_LABELS[codes[0]], LEVEL_LABELS[codes[-1]]
    return lo if lo == hi else f"{lo} à {hi}"


def matches_levels(levels: pd.Series, wanted: list[str], keep_unknown: bool) -> pd.Series:
    """Masque des offres qui citent au moins un des niveaux voulus (+ les non précisées)."""
    wanted_set = set(wanted)
    hit = levels.map(lambda s: isinstance(s, str) and bool(wanted_set & set(s.split(","))))
    if keep_unknown:
        hit |= levels.isna()
    return hit
