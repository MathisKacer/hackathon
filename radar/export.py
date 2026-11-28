"""T91 — Export des candidatures en CSV (ouvrable dans Excel, LibreOffice, Sheets).

Séparateur « ; » et UTF-8 avec BOM : Excel en français affiche alors bien les colonnes et les
accents. Les noms d'entreprise et les notes sont du texte libre : une cellule qui commencerait
comme une formule (=, +, -, @) est neutralisée par une apostrophe (injection CSV).
"""

from __future__ import annotations

import csv
import io
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Paris")
COLUMNS = (
    "Nom",
    "Type",
    "Statut",
    "Envoyée le",
    "Relancée le",
    "Ville",
    "Note",
    "Lien de l'offre",
)
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def _safe(value) -> str:
    text = "" if value is None else str(value)
    return "'" + text if text.startswith(FORMULA_START) else text


def _date(value) -> str:
    return value.astimezone(TZ).strftime("%d/%m/%Y") if value else ""


def candidatures_csv(favorites: list[dict]) -> bytes:
    """CSV des favoris cochés « Candidaté » (format de accounts.list_favorites).

    « Envoyée le » reste vide quand la date n'est pas connue (candidature d'avant T90).
    """
    out = io.StringIO()
    writer = csv.writer(out, delimiter=";", lineterminator="\r\n")
    writer.writerow(COLUMNS)
    for f in favorites:
        if not f.get("candidate"):
            continue
        details = f.get("details") or {}
        row = (
            f.get("label"),
            "Entreprise" if f.get("kind") == "entreprise" else "Offre",
            f.get("statut"),
            "" if f.get("date_estimee") else _date(f.get("envoyee_le")),
            _date(f.get("relancee_le")),
            details.get("commune"),
            f.get("note"),
            details.get("url"),
        )
        writer.writerow([_safe(v) for v in row])
    return out.getvalue().encode("utf-8-sig")
