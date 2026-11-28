"""T91 — export CSV des candidatures."""

import csv
import io
from datetime import UTC, datetime

from radar.export import COLUMNS, candidatures_csv


def _fav(**extra):
    base = {
        "kind": "entreprise",
        "label": "ACME",
        "candidate": True,
        "statut": "Envoyée",
        "note": "",
        "details": {"commune": "RENNES"},
        "envoyee_le": datetime(2026, 11, 27, 23, 30, tzinfo=UTC),
        "relancee_le": None,
        "date_estimee": False,
    }
    return base | extra


def _rows(data: bytes):
    assert data.startswith(b"\xef\xbb\xbf")  # BOM : accents lisibles dans Excel
    return list(csv.reader(io.StringIO(data.decode("utf-8-sig")), delimiter=";"))


def test_only_candidatures_with_paris_dates():
    rows = _rows(candidatures_csv([_fav(), _fav(label="Pas candidaté", candidate=False)]))
    assert rows[0] == list(COLUMNS) and len(rows) == 2
    assert rows[1] == ["ACME", "Entreprise", "Envoyée", "28/11/2026", "", "RENNES", "", ""]


def test_unknown_date_and_special_characters():
    fav = _fav(kind="offre", date_estimee=True, note='Appeler "Léa" ; lundi\nmatin', details={})
    row = _rows(candidatures_csv([fav]))[1]
    assert row[1] == "Offre" and row[3] == ""
    assert row[6] == 'Appeler "Léa" ; lundi\nmatin'


def test_formula_injection_is_neutralised():
    fav = _fav(label="=HYPERLINK(1)", note="+33 6", details={"commune": "@x"})
    row = _rows(candidatures_csv([fav]))[1]
    assert row[0] == "'=HYPERLINK(1)" and row[5] == "'@x" and row[6] == "'+33 6"


def test_empty():
    assert _rows(candidatures_csv([])) == [list(COLUMNS)]
