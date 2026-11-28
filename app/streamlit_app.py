"""Application Radar (Streamlit) : point d'entrée et navigation.

Lancer : uv run streamlit run app/streamlit_app.py

Trois pages (barre de navigation en haut) :
- Explorer (app/vues/explorer.py) : carte, candidatures spontanées et offres autour de soi ;
- Entreprises (app/vues/entreprises.py) : chercher une entreprise et ouvrir sa fiche ;
- Mon espace (app/vues/mon_espace.py) : compte facultatif, profil, historique des recherches.
Code partagé : app/commun.py (données, réglages du profil), app/carte.py (carte),
app/fiche_ui.py (fiche entreprise), app/compte.py (comptes).
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from commun import PAGES_DIR, init_defaults, persist_widget_state
from compte import _con, current_user
from entete import header
from style import inject_css

from radar import admin

# T93 (essai, branche emma/interface-riche) : logos « Compass » d'Emma (app/static/) : le mot
# dans notre barre du haut (app/entete.py) et en grand sur l'accueil, le C-boussole pour l'onglet.
STATIC = Path(__file__).resolve().parent / "static"
st.set_page_config(
    page_title="Compass", page_icon=str(STATIC / "icone-compass-clair.svg"), layout="wide"
)
inject_css()  # apparence commune (T70, app/style.py)
init_defaults()
persist_widget_state()  # garde la recherche quand on change de page

user = current_user()
n_fav = st.session_state.pop("_toast_favoris", 0)
if n_fav:
    s = "s" if n_fav > 1 else ""
    st.toast(f"{n_fav} favori{s} enregistré{s} dans ton compte.")
if n_lost := st.session_state.pop("_toast_recherches_perdues", 0):
    st.toast(f"{n_lost} recherche(s) non reprise(s) : tu as atteint le maximum.")
# T93 (essai) : page d'accueil, page de résultats, entreprises, compte ; navigation de
# Streamlit masquée, remplacée par notre barre du haut (app/entete.py).
is_admin = bool(user and admin.is_admin(_con(), user["id"]))
pages = {
    "accueil": st.Page(PAGES_DIR / "accueil.py", title="Accueil", default=True),
    "recherche": st.Page(PAGES_DIR / "explorer.py", title="Recherche", url_path="recherche"),
    "entreprises": st.Page(PAGES_DIR / "entreprises.py", title="Entreprises"),
    "compte": st.Page(
        PAGES_DIR / "mon_espace.py",
        title="Mon compte" if user else "Se connecter",
        url_path="mon-espace",
    ),
}
# T79 (D39) : page Administration, seulement pour les administrateurs (membres de l'équipe).
if is_admin:
    pages["admin"] = st.Page(
        PAGES_DIR / "administration.py", title="Administration", url_path="administration"
    )
page = st.navigation(list(pages.values()), position="hidden")
current = next(k for k, p in pages.items() if p == page)
header(pages, current, user, is_admin)
page.run()
