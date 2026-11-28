"""T93 (essai) — Page « S'inscrire » (création de compte seulement)."""

from __future__ import annotations

import streamlit as st
from commun import saved_profile_keys
from compte import signup_form
from entete import page
from style import hero

hero("S'inscrire", "Crée ton compte pour garder tes compétences, tes favoris et tes recherches.",
     compact=True)  # fmt: skip
_, mid, _ = st.columns([1, 1.4, 1])
with mid:
    with st.container(border=True, key="espace_inscription"):
        signup_form(saved_profile_keys(), go="compte")
    st.page_link(page("connexion"), label="Déjà un compte ? Se connecter")
