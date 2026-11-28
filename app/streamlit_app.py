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
from style import inject_css

from radar import admin

# T93 (essai, branche emma/interface-riche) : logo « Compass » (app/static/), version claire
# ou sombre selon le thème ; icône de l'onglet du navigateur.
STATIC = Path(__file__).resolve().parent / "static"
st.set_page_config(page_title="Compass", page_icon=str(STATIC / "compass_icone.svg"), layout="wide")
_dark = getattr(st.context.theme, "type", None) == "dark"
st.logo(
    str(STATIC / ("compass_logo_sombre.svg" if _dark else "compass_logo.svg")),
    size="large",
    icon_image=str(STATIC / "compass_icone.svg"),
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
pages = [
    st.Page(PAGES_DIR / "explorer.py", title="Explorer", icon=":material/explore:", default=True),
    st.Page(PAGES_DIR / "entreprises.py", title="Entreprises", icon=":material/apartment:"),
    st.Page(
        PAGES_DIR / "mon_espace.py",
        title=f"Mon espace ({user['username']})" if user else "Se connecter",
        icon=":material/person:",
        url_path="mon-espace",
    ),
]
# T79 (D39) : page Administration, seulement pour les administrateurs (membres de l'équipe).
if user and admin.is_admin(_con(), user["id"]):
    pages.append(
        st.Page(
            PAGES_DIR / "administration.py",
            title="Administration",
            icon=":material/admin_panel_settings:",
            url_path="administration",
        )
    )
st.navigation(pages, position="top").run()
