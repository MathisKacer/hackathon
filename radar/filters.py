"""Filtres « taille » et « secteur » des entreprises (T41).

    df = filter_companies(df, tailles=["50–249"], secteurs=["J", "M"])

- Taille : tranches lisibles regroupant les codes INSEE `tranche_effectif` (le référentiel
  ne garde que les établissements de 10 salariés et plus, T20).
- Secteur : section NAF (A à U), prise dans `naf_section` si le référentiel la fournit (T20),
  sinon déduite des deux premiers chiffres du code NAF (`62.02A` ou `6202A`).
Une liste vide = pas de filtre. Une entreprise de taille ou de secteur inconnu est écartée
dès qu'on filtre sur ce critère.
"""

from __future__ import annotations

import pandas as pd

# Tranche lisible → codes INSEE de tranche d'effectif.
TAILLES: dict[str, tuple[str, ...]] = {
    "10–49": ("11", "12"),
    "50–249": ("21", "22", "31"),
    "250–999": ("32", "41"),
    "1 000 et plus": ("42", "51", "52", "53"),
}
_TRANCHE_TO_TAILLE = {code: label for label, codes in TAILLES.items() for code in codes}

# Sections de la NAF rév. 2 (Insee), libellés raccourcis pour la barre latérale.
SECTIONS: dict[str, str] = {
    "A": "Agriculture, sylviculture, pêche",
    "B": "Industries extractives",
    "C": "Industrie manufacturière",
    "D": "Énergie (électricité, gaz)",
    "E": "Eau, déchets, dépollution",
    "F": "Construction",
    "G": "Commerce, réparation auto",
    "H": "Transports et entreposage",
    "I": "Hébergement et restauration",
    "J": "Information et communication",
    "K": "Finance et assurance",
    "L": "Immobilier",
    "M": "Activités spécialisées, scientifiques et techniques",
    "N": "Services administratifs et de soutien",
    "O": "Administration publique",
    "P": "Enseignement",
    "Q": "Santé humaine et action sociale",
    "R": "Arts, spectacles, loisirs",
    "S": "Autres activités de services",
    "T": "Ménages employeurs",
    "U": "Activités extra-territoriales",
}
# Division NAF (2 chiffres) → section : bornes de début de chaque section.
_SECTION_STARTS = [
    (1, "A"),
    (5, "B"),
    (10, "C"),
    (35, "D"),
    (36, "E"),
    (41, "F"),
    (45, "G"),
    (49, "H"),
    (55, "I"),
    (58, "J"),
    (64, "K"),
    (68, "L"),
    (69, "M"),
    (77, "N"),
    (84, "O"),
    (85, "P"),
    (86, "Q"),
    (90, "R"),
    (94, "S"),
    (97, "T"),
    (99, "U"),
]


def size_bucket(tranche: str | None) -> str | None:
    """Code INSEE de tranche d'effectif ('21') → tranche lisible ('50–249'), None si inconnu."""
    if tranche is None or pd.isna(tranche):
        return None
    return _TRANCHE_TO_TAILLE.get(str(tranche).strip())


def naf_section(naf: str | None) -> str | None:
    """Code NAF ('62.02A' ou '6202A') → section ('J'), None si illisible."""
    if naf is None or pd.isna(naf):
        return None
    digits = str(naf).replace(".", "").strip()[:2]
    if not digits.isdigit():
        return None
    division = int(digits)
    section = None
    for start, letter in _SECTION_STARTS:
        if division >= start:
            section = letter
    return section


def company_sections(df: pd.DataFrame) -> pd.Series:
    """Section NAF de chaque entreprise (colonne `naf_section`, complétée depuis `naf`)."""
    from_naf = (
        df["naf"].map(naf_section) if "naf" in df else pd.Series(None, index=df.index, dtype=object)
    )
    if "naf_section" in df:
        return df["naf_section"].where(df["naf_section"].notna(), from_naf)
    return from_naf


def filter_companies(
    df: pd.DataFrame, tailles: list[str] | None = None, secteurs: list[str] | None = None
) -> pd.DataFrame:
    """Garde les entreprises dont la taille et le secteur sont dans les listes (vide = tout)."""
    out = df
    if tailles and not out.empty:
        sizes = (
            out["tranche_effectif"].map(size_bucket) if "tranche_effectif" in out else pd.Series()
        )
        out = out[sizes.reindex(out.index).isin(tailles)]
    if secteurs and not out.empty:
        out = out[company_sections(out).isin(secteurs)]
    return out
