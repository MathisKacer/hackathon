"""Recherches enregistrées (T84) : base, limite de 20, visite anonyme, bouton, relance."""

from pathlib import Path

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
BUTTON = (
    HEADER
    + """
from recherches import save_button
st.session_state.setdefault("contrat", "Stage")
save_button({"contrat": ["Tous", "Stage"]})
"""
)


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(accounts, "DB_PATH", tmp_path / "radar.db")
    st.cache_resource.clear()
    yield
    st.cache_resource.clear()


def _user(name="celia"):
    con = accounts.connect()
    return con, accounts.create_user(con, name, "Radar-Demo-2026")


def _fill(con, uid, n):
    for i in range(n):
        accounts.save_search(con, uid, f"r{i}", {"rayon": i})


def _submit(at):
    next(b for b in at.button if b.label == "Enregistrer").click()
    at.run()


def test_save_list_delete_and_no_duplicate():
    con, uid = _user()
    assert accounts.save_search(con, uid, "  Stage   Rennes ", {"contrat": "Stage"})
    assert not accounts.save_search(con, uid, "autre nom", {"contrat": "Stage"})
    [s] = accounts.list_saved_searches(con, uid)
    assert s["nom"] == "Stage Rennes" and s["params"] == {"contrat": "Stage"}
    assert set(s) == {"id", "nom", "params", "created_at"}  # ni entreprises ni résultats
    accounts.delete_saved_search(con, uid, s["id"])
    assert accounts.list_saved_searches(con, uid) == []


def test_limit_of_20_isolation_and_cascade():
    con, uid = _user()
    other = accounts.create_user(con, "mathis", "Autre-Compte-42")
    _fill(con, uid, accounts.SAVED_SEARCH_MAX)
    with pytest.raises(accounts.AccountError, match="supprimes-en une"):
        accounts.save_search(con, uid, "21e", {"rayon": 999})
    first = accounts.list_saved_searches(con, uid)[0]
    accounts.delete_saved_search(con, other, first["id"])  # pas le sien : sans effet
    assert len(accounts.list_saved_searches(con, uid)) == accounts.SAVED_SEARCH_MAX
    accounts.delete_saved_search(con, uid, first["id"])
    assert accounts.save_search(con, uid, "21e", {"rayon": 999})
    accounts.delete_user(con, uid)
    assert con.execute("SELECT count(*) FROM recherches_enregistrees").fetchone()[0] == 0


def test_button_shows_message_at_the_21st():
    con, uid = _user()
    _fill(con, uid, accounts.SAVED_SEARCH_MAX)
    at = AppTest.from_string(BUTTON, default_timeout=30)
    at.session_state["compte_user"] = {"id": uid, "username": "celia"}
    at.run()
    _submit(at)
    assert any("supprimes-en une" in e.value for e in at.error)
    assert len(accounts.list_saved_searches(con, uid)) == accounts.SAVED_SEARCH_MAX


def test_anonymous_keeps_in_session_then_saved_at_login(tmp_path):
    at = AppTest.from_string(BUTTON, default_timeout=30)
    at.run()
    _submit(at)
    [temp] = at.session_state["_recherches_temporaires"]
    assert temp["nom"] == "Stage" or temp["nom"].startswith("Stage")
    assert not (tmp_path / "radar.db").exists()  # sans compte : rien sur le disque

    con, uid = _user()
    login = AppTest.from_string(HEADER + "from compte import login_forms\nlogin_forms({})\n")
    login.session_state["_recherches_temporaires"] = [temp]
    login.run()
    login.text_input[0].input("celia")
    login.text_input[1].input("Radar-Demo-2026")
    next(b for b in login.button if b.label == "Se connecter").click()
    login.run()
    assert [s["params"] for s in accounts.list_saved_searches(con, uid)] == [{"contrat": "Stage"}]


def test_relaunch_and_delete_from_mon_espace():
    con, uid = _user()
    accounts.save_search(con, uid, "Mon alternance", {"contrat": "Alternance"})
    script = (
        HEADER
        + """
from recherches import saved_section
st.session_state.setdefault("contrat", "Tous")
saved_section({"contrat": ["Tous", "Alternance"]})
"""
    )
    at = AppTest.from_string(script, default_timeout=30)
    at.session_state["compte_user"] = {"id": uid, "username": "celia"}
    at.run()
    assert any("Mon alternance" in m.value for m in at.markdown)
    next(b for b in at.button if b.label == "Relancer").click()
    at.run()
    assert at.session_state["contrat"] == "Alternance"
    next(b for b in at.button if b.label == "Supprimer").click()
    at.run()
    assert accounts.list_saved_searches(con, uid) == []


def test_explorer_no_longer_records_automatically():
    source = (Path(__file__).resolve().parents[1] / "app" / "vues" / "explorer.py").read_text()
    assert "record_search" not in source and "save_button(" in source
