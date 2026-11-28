"""T93 (essai, branche emma/interface-riche) — Page d'accueil de Compass.

Le logo en grand et le slogan, une phrase qui dit ce que fait le site, la recherche au centre
(ville, contrat, domaine, rayon : mêmes réglages que la page de résultats, gardés d'une page à
l'autre) et un lien « Chercher par entreprise ».
"""

from __future__ import annotations

import streamlit as st
from commun import CONTRATS, DOMAINES, DOMAINS, RAYONS, get_communes
from entete import go, logo_svg, page

SLOGAN = "Oser l'audace, fini l'impasse"
PITCH = "Trouver les offres avant qu'elles paraissent"

st.markdown(
    f"<div class='accueil-head'><div class='accueil-logo'>{logo_svg()}</div>"
    f"<div class='accueil-slogan'>{SLOGAN}</div></div>"
    f"<p class='accueil-pitch'>{PITCH}</p>",
    unsafe_allow_html=True,
)

_, mid, _ = st.columns([1, 2.4, 1])
with mid:
    with st.container(border=True, key="carte_recherche_accueil"):
        st.selectbox(
            "Où ?",
            get_communes()["label"].tolist(),
            index=None,
            key="ville",
            placeholder="Ta ville ou ton code postal (vide : toute la France)",
        )
        c1, c2, c3 = st.columns([2.2, 2, 1], vertical_alignment="bottom")
        c1.segmented_control("Contrat", CONTRATS, key="contrat", required=True)
        c2.selectbox("Domaine", DOMAINES, key="domaine", format_func=lambda k: DOMAINS[k].label)
        c3.selectbox("Rayon", RAYONS, key="rayon", format_func=lambda r: f"{r} km")
        # Rappel : la page de résultats s'ouvre au passage suivant (app/streamlit_app.py)
        st.button(
            "Rechercher",
            type="primary",
            icon=":material/search:",
            width="stretch",
            on_click=go,
            args=("recherche",),
        )
    with st.container(key="lien_entreprise"):
        st.page_link(
            page("entreprises"),
            label="Chercher par entreprise",
            icon=":material/apartment:",
        )
