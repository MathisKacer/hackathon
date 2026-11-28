"""T93 (essai) — Page « Se connecter » (sans le formulaire d'inscription, qui a sa page)."""

from __future__ import annotations

import streamlit as st
from commun import saved_profile_keys
from compte import login_form
from entete import page
from style import hero

hero("Se connecter", "Retrouve tes compétences, tes favoris et tes recherches.", compact=True)
_, mid, _ = st.columns([1, 1.4, 1])
with mid:
    with st.container(border=True, key="espace_connexion"):
        login_form(saved_profile_keys(), go="compte")
    with st.container(key="lien_autre_page"):
        st.page_link(page("inscription"), label="Si vous n'avez pas de compte, inscrivez-vous")
