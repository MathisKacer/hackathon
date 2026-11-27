"""Département → région (libellés des régions tels qu'Adzuna les utilise, cf. collect/adzuna.py)."""

from __future__ import annotations

_REGIONS: dict[str, list[str]] = {
    "Auvergne-Rhône-Alpes": ["01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74"],  # noqa: E501
    "Bourgogne-Franche-Comté": ["21", "25", "39", "58", "70", "71", "89", "90"],
    "Bretagne": ["22", "29", "35", "56"],
    "Centre-Val de Loire": ["18", "28", "36", "37", "41", "45"],
    "Corse": ["2A", "2B", "20"],
    "Grand Est": ["08", "10", "51", "52", "54", "55", "57", "67", "68", "88"],
    "Hauts-de-France": ["02", "59", "60", "62", "80"],
    "Ile-de-France": ["75", "77", "78", "91", "92", "93", "94", "95"],
    "Normandie": ["14", "27", "50", "61", "76"],
    "Nouvelle-Aquitaine": ["16", "17", "19", "23", "24", "33", "40", "47", "64", "79", "86", "87"],
    "Occitanie": ["09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82"],
    "Pays de la Loire": ["44", "49", "53", "72", "85"],
    "Provence-Alpes-Côte d'Azur": ["04", "05", "06", "13", "83", "84"],
}  # fmt: skip

DEPT_TO_REGION: dict[str, str] = {d: r for r, depts in _REGIONS.items() for d in depts}


def region_of(departement: str | None) -> str | None:
    """Région d'un code département ('35', '2A', '974'…) ; None pour l'outre-mer / inconnu."""
    if not isinstance(departement, str):
        return None
    return DEPT_TO_REGION.get(departement)
