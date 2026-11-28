"""T93 (essai) — Page « S'inscrire » : ce qu'apporte un compte, et le formulaire."""

from __future__ import annotations

import streamlit as st
from commun import saved_profile_keys
from compte import signup_form
from entete import page
from style import hero

hero("S'inscrire", "Crée ton compte pour garder tes compétences, tes favoris et tes recherches.")
left, right = st.columns([1, 1], gap="large")
with left:
    st.markdown("#### Pourquoi créer un compte ?")
    for icon, title, text in (
        ("star", "Garder tes favoris", "entreprises et offres, d'une visite à l'autre."),
        ("send", "Suivre tes candidatures", "envoyée, relancée, entretien, réponse."),
        ("history", "Retrouver tes recherches", "et les relancer en un clic."),
        ("badge", "Garder tes compétences", "tirées de ton CV."),
    ):
        st.markdown(f":material/{icon}: **{title}** : {text}")
    st.caption("Compass marche aussi sans compte : dans ce cas, rien n'est enregistré.")
with right:
    with st.container(border=True, key="espace_inscription"):
        signup_form(saved_profile_keys(), go="compte")
    with st.container(key="lien_autre_page"):
        st.page_link(page("connexion"), label="Si vous avez déjà un compte, connectez-vous")
