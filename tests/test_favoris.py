"""Favoris (T54) côté interface : temporaires en anonyme, repris à la connexion, étoile, offres."""

from datetime import timedelta

import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from radar import accounts

HEADER = """
import sys
from pathlib import Path
import streamlit as st
sys.path.insert(0, str(Path.cwd() / "app"))
"""


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(accounts, "DB_PATH", tmp_path / "radar.db")
    monkeypatch.setattr(accounts, "SEARCH_MERGE_WINDOW", timedelta(0))
    st.cache_resource.clear()
    yield
    st.cache_resource.clear()


def test_star_toggles_temporary_favorite_without_writing_to_disk(tmp_path):
    script = (
        HEADER
        + """
from favoris import star_button, favorites
star_button("entreprise", "111", "ACME", {"commune": "RENNES"}, key="s")
st.write(len(favorites("entreprise")))
"""
    )
    at = AppTest.from_string(script, default_timeout=30)
    at.run()
    assert at.button(key="s").label == "☆ Ajouter aux favoris"
    at.button(key="s").click()
    at.run()
    assert at.button(key="s").label == "★ Dans mes favoris"
    assert ("entreprise", "111") in at.session_state["_favoris_temporaires"]
    assert not (tmp_path / "radar.db").exists()  # anonyme : rien sur le disque
    at.button(key="s").click()
    at.run()
    assert at.button(key="s").label == "☆ Ajouter aux favoris"


def test_temporary_favorites_saved_at_login():
    uid = accounts.create_user(accounts.connect(), "celia", "Radar-Demo-2026")
    script = (
        HEADER
        + """
from compte import login_forms
login_forms({})
"""
    )
    at = AppTest.from_string(script, default_timeout=30)
    at.session_state["_favoris_temporaires"] = {
        ("entreprise", "111"): {"label": "ACME", "details": {}},
        ("offre", "adzuna:1"): {"label": "Stage data", "details": {"url": "https://ex.org"}},
    }
    at.run()
    at.text_input[0].input("celia")
    at.text_input[1].input("Radar-Demo-2026")
    next(b for b in at.button if b.label == "Se connecter").click()
    at.run()
    favs = accounts.list_favorites(accounts.connect(), uid)
    assert {(f["kind"], f["ref"]) for f in favs} == {("entreprise", "111"), ("offre", "adzuna:1")}
    temp = (
        at.session_state["_favoris_temporaires"]
        if "_favoris_temporaires" in at.session_state
        else {}
    )
    assert not temp  # la mémoire temporaire est vidée
    assert at.session_state["_toast_favoris"] == 2


def test_connected_star_writes_to_account():
    uid = accounts.create_user(accounts.connect(), "celia", "Radar-Demo-2026")
    script = (
        HEADER
        + """
from favoris import star_button
star_button("entreprise", "222", "BETA", key="s")
"""
    )
    at = AppTest.from_string(script, default_timeout=30)
    at.session_state["compte_user"] = {"id": uid, "username": "celia"}
    at.run()
    at.button(key="s").click()
    at.run()
    assert accounts.favorite_refs(accounts.connect(), uid, "entreprise") == {"222"}


def test_sync_offers_editor(monkeypatch):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
    import favoris

    added, removed = [], []
    monkeypatch.setattr(favoris, "add", lambda k, r, label, d: added.append((k, r, label)))
    monkeypatch.setattr(favoris, "remove", lambda k, r: removed.append((k, r)))
    offers = pd.DataFrame(
        {
            "source": ["adzuna", "adzuna"],
            "offre_id": ["1", "2"],
            "titre": ["Stage data", "Data analyst"],
            "entreprise_nom": ["ACME", "BETA"],
            "url": ["https://ex.org/1", None],
            "commune": ["Rennes", "Bruz"],
            "contrat": ["stage", "emploi"],
            "date_publication": ["2026-11-20", "2026-11-21"],
        },
        index=[10, 11],
    )
    before = pd.DataFrame({"★": [False, True]}, index=[10, 11])
    after = pd.DataFrame({"★": [True, False]}, index=[10, 11])
    assert favoris.sync_offers_editor(after, before, offers)
    assert added == [("offre", "adzuna:1", "Stage data — ACME")]
    assert removed == [("offre", "adzuna:2")]
    assert not favoris.sync_offers_editor(before, before, offers)
