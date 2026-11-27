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

import streamlit as st
from commun import PAGES_DIR, init_defaults, persist_widget_state
from compte import current_user

st.set_page_config(page_title="Radar", page_icon="🧭", layout="wide")

init_defaults()
persist_widget_state()  # garde la recherche quand on change de page

user = current_user()
n_fav = st.session_state.pop("_toast_favoris", 0)
if n_fav:
    s = "s" if n_fav > 1 else ""
    st.toast(f"{n_fav} favori{s} enregistré{s} dans ton compte.")
pages = [
    st.Page(PAGES_DIR / "explorer.py", title="Explorer", default=True),
    st.Page(PAGES_DIR / "entreprises.py", title="Entreprises"),
    st.Page(
        PAGES_DIR / "mon_espace.py",
        title=f"Mon espace ({user['username']})" if user else "Se connecter",
        url_path="mon-espace",
    ),
]
st.navigation(pages, position="top").run()
