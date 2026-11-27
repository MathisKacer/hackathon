"""Tests du collecteur Adzuna, sans appel réseau."""

from radar.collect import adzuna
from radar.collect.adzuna import COLUMNS, Quota, _to_row

SAMPLE = {
    "id": "123",
    "title": "Stage Data Analyst H/F",
    "description": "Au sein de l'équipe data…",
    "created": "2026-11-20T10:00:00Z",
    "company": {"display_name": "ACME"},
    "location": {
        "display_name": "Rennes, Ille-et-Vilaine",
        "area": ["France", "Bretagne", "Ille-et-Vilaine", "Rennes"],
    },
    "latitude": 48.11,
    "longitude": -1.68,
    "contract_type": None,
    "contract_time": "full_time",
    "category": {"label": "Emplois Informatique"},
    "redirect_url": "https://example.org/offre/123",
    "salary_is_predicted": "1",
}  # fmt: skip


def test_to_row_matches_contract_columns():
    row = _to_row(SAMPLE, "data", "Bretagne", "2026-11-27T12:00:00+00:00")
    assert list(row) == COLUMNS
    assert row["source"] == "adzuna"
    assert row["entreprise_nom"] == "ACME"
    assert row["commune"] == "Rennes"
    assert row["zone"] == "France > Bretagne > Ille-et-Vilaine > Rennes"
    assert row["siret"] is None
    assert row["salaire_predit"] is True


def test_to_row_handles_missing_fields():
    row = _to_row({"id": 1}, "data", None, "t")
    assert row["entreprise_nom"] is None and row["commune"] is None and row["zone"] == ""


def test_quota_counts_and_limits(tmp_path, monkeypatch):
    monkeypatch.setattr(Quota, "path", tmp_path / "quota.json")
    q = Quota(daily_limit=2)
    assert q.remaining == 2
    q.record()
    q.record()
    assert q.used_today == 2 and q.remaining == 0


def test_regions_start_with_priorities():
    assert adzuna.REGIONS[:2] == ["Bretagne", "Ile-de-France"]
