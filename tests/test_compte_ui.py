"""Parcours du bloc compte dans Streamlit (T48), avec AppTest et une base temporaire.

La mini-app reproduit le branchement de app/streamlit_app.py : bloc compte, puis widgets
de recherche portant les clés du profil.
"""

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from radar import accounts


def _mini_app():
    import sys
    from pathlib import Path

    import streamlit as st

    sys.path.insert(0, str(Path.cwd() / "app"))
    from compte import account_sidebar

    keys = {"contrat": ["Tous", "Stage", "Alternance"], "regions": ["Bretagne", "Normandie"]}
    with st.sidebar:
        account_sidebar(keys)
        st.radio("Contrat visé", keys["contrat"], key="contrat")
        st.multiselect("Régions", keys["regions"], key="regions")


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(accounts, "DB_PATH", tmp_path / "radar.db")
    st.cache_resource.clear()  # oublie la connexion d'un test précédent
    at = AppTest.from_function(_mini_app, default_timeout=30)
    at.run()
    yield at
    st.cache_resource.clear()


def test_anonymous_by_default_writes_nothing(app, tmp_path):
    assert any("Mode démo anonyme" in c.value for c in app.sidebar.caption)
    assert "compte_user" not in app.session_state
    con = accounts.connect(tmp_path / "radar.db")
    assert con.execute("SELECT count(*) FROM users").fetchone()[0] == 0


def _signup(at, username="celia", password="motdepasse1", confirm=None):
    texts = at.sidebar.text_input
    # onglet « Créer un compte » : 2e formulaire (identifiant, mot de passe, confirmation)
    texts[2].input(username)
    texts[3].input(password)
    texts[4].input(confirm or password)
    next(b for b in at.sidebar.button if b.label == "Créer mon compte").click()
    at.run()


def _login(at, username, password):
    texts = at.sidebar.text_input
    texts[0].input(username)
    texts[1].input(password)
    next(b for b in at.sidebar.button if b.label == "Se connecter").click()
    at.run()


def _button(at, label):
    next(b for b in at.sidebar.button if b.label == label).click()
    at.run()


def test_signup_saves_settings_then_login_restores_them(app):
    app.sidebar.radio[0].set_value("Stage")
    app.sidebar.multiselect[0].set_value(["Bretagne"])
    app.run()
    _signup(app)
    assert app.session_state["compte_user"]["username"] == "celia"

    _button(app, "Se déconnecter")
    assert "compte_user" not in app.session_state
    app.sidebar.radio[0].set_value("Tous")
    app.sidebar.multiselect[0].set_value([])
    app.run()

    _login(app, "celia", "motdepasse1")
    assert app.session_state["compte_user"]["username"] == "celia"
    assert app.sidebar.radio[0].value == "Stage"
    assert app.sidebar.multiselect[0].value == ["Bretagne"]
    assert not app.exception


def test_save_button_updates_profile(app):
    _signup(app)
    app.sidebar.radio[0].set_value("Alternance")
    app.run()
    _button(app, "💾 Enregistrer")
    uid = app.session_state["compte_user"]["id"]
    assert accounts.load_profile(accounts.connect(), uid)["contrat"] == "Alternance"


def test_wrong_password_and_mismatch(app):
    _signup(app, confirm="different1")
    assert any("ne correspondent pas" in e.value for e in app.sidebar.error)
    _signup(app)
    _button(app, "Se déconnecter")
    _login(app, "celia", "mauvais-mdp")
    assert "compte_user" not in app.session_state
    assert any("incorrect" in e.value for e in app.sidebar.error)


def test_delete_account(app):
    _signup(app)
    delete = next(b for b in app.sidebar.button if b.label == "Supprimer")
    assert delete.disabled  # tant que la case n'est pas cochée
    app.sidebar.checkbox[0].check()
    app.run()
    _button(app, "Supprimer")
    assert "compte_user" not in app.session_state
    assert accounts.authenticate(accounts.connect(), "celia", "motdepasse1") is None


def test_full_app_runs_with_account_box(tmp_path, monkeypatch):
    """Lance le vrai app/streamlit_app.py sur des offres factices (dossier temporaire)."""
    from dataclasses import replace

    from radar.fake_data import generate
    from radar.process import quick_filter

    raw = tmp_path / "raw" / "offres_raw"
    raw.mkdir(parents=True)
    offers = generate(n_entreprises=200, seed=0).offres_raw["adzuna"]
    # comme les vraies offres Adzuna : région de la requête, date de collecte en texte
    offers = offers.assign(
        region_requete="Bretagne", date_collecte=offers["date_collecte"].astype(str)
    )
    offers.to_parquet(raw / "adzuna.parquet")
    monkeypatch.setattr(quick_filter, "PATHS", replace(quick_filter.PATHS, raw=tmp_path / "raw"))
    monkeypatch.setattr(accounts, "DB_PATH", tmp_path / "radar.db")
    monkeypatch.syspath_prepend("app")
    st.cache_data.clear()
    st.cache_resource.clear()

    at = AppTest.from_file("../app/streamlit_app.py", default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    assert any("Mode démo anonyme" in c.value for c in at.sidebar.caption)
    assert at.sidebar.radio(key="contrat").value == "Tous"
    assert at.sidebar.slider(key="max_age").value == 60
    assert not at.warning  # pas d'avertissement « valeur par défaut + session_state »
    st.cache_data.clear()
    st.cache_resource.clear()
