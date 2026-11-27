"""Tests du collecteur La bonne alternance, sans appel réseau."""

import json

from radar.collect import lba
from radar.collect.lba import COLUMNS, RECRUTEURS_COLUMNS, job_to_row, split_address, split_items

WORKPLACE = {
    "name": "ACME Data",
    "legal_name": "ACME SAS",
    "siret": "12345678900011",
    "size": "50-99",
    "website": "https://example.org",
    "location": {
        "address": "12 rue de la Donnée 35000 Rennes",
        "geopoint": {"type": "Point", "coordinates": [-1.68, 48.11]},
    },
    "domain": {"idcc": 1486, "opco": "ATLAS", "naf": {"code": "6201Z", "label": "Programmation"}},
}
JOB = {
    "identifier": {"id": "abc", "partner_job_id": "p1", "partner_label": "La bonne alternance"},
    "workplace": WORKPLACE,
    "apply": {"url": "https://example.org/postuler", "phone": "0600000000"},
    "contract": {"type": ["Apprentissage"], "duration": 24, "remote": "hybrid"},
    "offer": {
        "title": "Alternance Data Analyst",
        "description": "…",
        "rome_codes": ["M1419", "M1405"],
        "publication": {"creation": "2026-11-01T00:00:00Z", "expiration": "2027-01-01T00:00:00Z"},
        "target_diploma": {"european": "7", "label": "Master"},
        "status": "Active",
        "opening_count": 2,
    },
    "is_delegated": False,
}
RECRUITER = {"identifier": {"id": "r1"}, "workplace": WORKPLACE, "apply": {"url": "u"}}


def test_job_to_row_matches_contract():
    row = job_to_row(JOB, "t")
    assert list(row) == COLUMNS
    assert row["source"] == "lba" and row["siret"] == "12345678900011"
    assert (row["lat"], row["lon"]) == (48.11, -1.68)  # GeoJSON [lon, lat] inversé
    assert (row["code_postal"], row["commune"]) == ("35000", "Rennes")
    assert row["code_rome"] == "M1419,M1405" and row["contrat_brut"] == "Apprentissage"
    assert row["naf"] == "6201Z" and row["delegue_ecole"] is False
    assert "0600000000" not in json.dumps(row)  # le téléphone n'est jamais conservé


def test_job_to_row_handles_missing_fields():
    row = job_to_row({"offer": {"title": "x"}}, "t")
    assert row["siret"] is None and row["lat"] is None and row["commune"] is None


def test_split_address():
    assert split_address("1 AV DU GENERAL 75008 PARIS 8") == ("75008", "PARIS 8")
    assert split_address("ZA de la Lande, 35510 Cesson-Sévigné") == ("35510", "Cesson-Sévigné")
    assert split_address(None) == (None, None)


def test_split_items_both_shapes():
    assert split_items({"jobs": [JOB], "recruiters": [RECRUITER]}) == ([JOB], [RECRUITER])
    assert split_items([JOB, RECRUITER]) == ([JOB], [RECRUITER])


def test_collect_from_export_file(tmp_path):
    f = tmp_path / "export.json"
    f.write_text(json.dumps([JOB, JOB, RECRUITER]), encoding="utf-8")
    offres, recs = lba.collect_from_export(f)
    assert len(offres) == 1 and len(recs) == 1  # doublons supprimés
    assert list(recs.columns) == RECRUTEURS_COLUMNS
    assert recs.loc[0, "siret"] == "12345678900011"


def test_departements_cover_france():
    assert len(lba.DEPARTEMENTS) == 101 and "2A" in lba.DEPARTEMENTS and "35" in lba.DEPARTEMENTS
