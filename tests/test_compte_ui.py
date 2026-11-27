"""Parcours du bloc compte (T48) dans Streamlit, avec AppTest.

La mini-app reproduit le branchement de app/streamlit_app.py : bloc compte, widgets de
recherche portant les clés du profil.
Base temporaire, jamais data/app/radar.db.
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


def _signup(at, username="celia", password="Radar-Demo-2026", confirm=None):
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

    _login(app, "celia", "Radar-Demo-2026")
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
    _signup(app, confirm="Different-Mdp-9")
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
    assert accounts.authenticate(accounts.connect(), "celia", "Radar-Demo-2026") is None


def test_weak_password_rejected_with_explanation(app):
    _signup(app, password="motdepasse1")
    assert "compte_user" not in app.session_state
    assert any("12 caractères" in e.value for e in app.sidebar.error)


def test_lockout_survives_page_reload(app):
    _signup(app)
    _button(app, "Se déconnecter")
    for _ in range(accounts.LOGIN_MAX_FAILS):
        _login(app, "celia", "mauvais")
    _login(app, "celia", "Radar-Demo-2026")  # bon mot de passe, mais compte bloqué
    assert "compte_user" not in app.session_state
    assert any("bloqué jusqu'à" in e.value for e in app.sidebar.error)
    # « recharger la page » = nouvelle session : toujours bloqué
    fresh = AppTest.from_function(_mini_app, default_timeout=30)
    fresh.run()
    _login(fresh, "celia", "Radar-Demo-2026")
    assert "compte_user" not in fresh.session_state
    assert any("bloqué jusqu'à" in e.value for e in fresh.sidebar.error)


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

    from pathlib import Path

    app_dir = Path(__file__).resolve().parents[1] / "app"
    at = AppTest.from_file(str(app_dir / "streamlit_app.py"), default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    # Page Explorer par défaut, recherche en haut (plus de barre latérale)
    assert any("<h1>Où candidater ?</h1>" in m.value for m in at.markdown)  # bandeau (T70)
    assert at.segmented_control(key="contrat").value == "Tous"
    assert at.slider(key="max_age").value == 60  # dans le panneau « Filtres »
    assert not at.warning  # pas d'avertissement « valeur par défaut + session_state »

    # Connecté : rien n'est enregistré tout seul (T84) ; Mon espace s'affiche
    uid = accounts.create_user(accounts.connect(), "celia", "Radar-Demo-2026")
    at.session_state["compte_user"] = {"id": uid, "username": "celia"}
    at.run()
    assert not at.exception, at.exception
    assert accounts.list_saved_searches(accounts.connect(), uid) == []
    at.switch_page(str(app_dir / "vues" / "mon_espace.py"))
    at.run()
    assert not at.exception, at.exception
    assert any("<h1>Bonjour celia</h1>" in m.value for m in at.markdown)
    assert any(s.value == "Mes compétences" for s in at.subheader)  # T81 : profil = compétences
    st.cache_data.clear()
    st.cache_resource.clear()


# --- T81 : le profil ne garde que les compétences (page Mon espace) ----------------------------


def _page_app():
    import sys
    from pathlib import Path

    import streamlit as st

    sys.path.insert(0, str(Path.cwd() / "app"))
    from compte import account_page

    keys = {"contrat": ["Tous", "Stage"], "competences": ["Python", "SQL", "R"]}
    st.session_state.setdefault("contrat", "Tous")
    st.session_state.setdefault("competences", [])
    account_page(keys, {"contrat": "Contrat", "competences": "Compétences"},
                 saved_keys={"competences": keys["competences"]})  # fmt: skip


@pytest.fixture
def page(tmp_path, monkeypatch):
    monkeypatch.setattr(accounts, "DB_PATH", tmp_path / "radar.db")
    st.cache_resource.clear()
    uid = accounts.create_user(accounts.connect(), "emma", "Radar-Demo-2026")
    accounts.save_profile(accounts.connect(), uid, {"contrat": "Stage", "rayon": 20})  # ancien
    at = AppTest.from_function(_page_app, default_timeout=30)
    at.session_state["compte_user"] = {"id": uid, "username": "emma"}
    at.session_state["contrat"] = "Tous"
    at.session_state["competences"] = ["Python", "R"]
    at.run()
    yield at, uid
    st.cache_resource.clear()


def test_profile_shows_only_skills_without_button(page):
    at, uid = page
    assert not at.exception
    assert any(s.value == "Mes compétences" for s in at.subheader)
    texts = [m.value for m in at.markdown] + [c.value for c in at.caption]
    assert not any("Contrat" in x for x in texts)  # l'ancien réglage du profil n'est pas affiché
    assert not any("Enregistrer" in b.label for b in at.button)  # T86 : plus de bouton


def test_login_restores_only_skills(tmp_path, monkeypatch):
    monkeypatch.setattr(accounts, "DB_PATH", tmp_path / "radar.db")
    st.cache_resource.clear()
    con = accounts.connect()
    uid = accounts.create_user(con, "emma", "Radar-Demo-2026")
    accounts.save_profile(con, uid, {"contrat": "Stage", "competences": ["SQL"]})
    at = AppTest.from_function(_page_app, default_timeout=30)
    at.run()
    at.text_input[0].input("emma")
    at.text_input[1].input("Radar-Demo-2026")
    next(b for b in at.button if b.label == "Se connecter").click()
    at.run()
    assert at.session_state["competences"] == ["SQL"]
    assert at.session_state["contrat"] == "Tous"  # l'ancien réglage du profil est ignoré
    st.cache_resource.clear()


def _page_app_editor():
    import sys
    from pathlib import Path

    import streamlit as st

    sys.path.insert(0, str(Path.cwd() / "app"))
    from compte import account_page
    from cv_ui import profile_skills_editor

    st.session_state.setdefault("competences", [])
    account_page({"competences": None}, {"competences": "Compétences"},
                 saved_keys={"competences": None},
                 profile_editor=profile_skills_editor)  # fmt: skip


def test_profile_skills_one_by_one(tmp_path, monkeypatch):
    """T86 : ✕ retire une compétence, l'ajout l'enregistre aussitôt ; dépôt du CV présent."""
    monkeypatch.setattr(accounts, "DB_PATH", tmp_path / "radar.db")
    st.cache_resource.clear()
    con = accounts.connect()
    uid = accounts.create_user(con, "emma", "Radar-Demo-2026")
    accounts.save_profile(con, uid, {"competences": ["Python", "R", "SQL"]})
    at = AppTest.from_function(_page_app_editor, default_timeout=30)
    at.session_state["compte_user"] = {"id": uid, "username": "emma"}
    at.session_state["competences"] = ["Python", "R", "SQL"]
    at.run()
    assert not at.exception
    assert at.get("file_uploader")  # dépôt du CV dans la partie compétences
    assert not any("Enregistrer" in b.label for b in at.button)
    labels = [b.label for b in at.button]
    assert {"Python", "R", "SQL"} <= set(labels)  # une étiquette ✕ par compétence

    next(b for b in at.button if b.label == "R").click()
    at.run()
    assert accounts.load_profile(accounts.connect(), uid)["competences"] == ["Python", "SQL"]
    assert at.session_state["competences"] == ["Python", "SQL"]  # recherche en cours aussi

    # (une compétence tapée hors de la liste passe par le même rappel ; l'outil de test ne
    # sait choisir que des options existantes : nettoyage testé dans test_competences.py)
    at.selectbox(key="competence_ajout").set_value("Excel")
    at.run()
    assert not at.exception
    saved = accounts.load_profile(accounts.connect(), uid)["competences"]
    assert saved == ["Python", "SQL", "Excel"]
    assert at.selectbox(key="competence_ajout").value is None  # le champ se vide
    assert "Excel" in [b.label for b in at.button]
    st.cache_resource.clear()
