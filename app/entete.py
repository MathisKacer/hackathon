"""T93 (essai, branche emma/interface-riche) — Barre du haut de Compass.

Streamlit place sa navigation à gauche ; on la masque (`position="hidden"`) et on dessine notre
barre : le logo à gauche (lien vers l'accueil, sauf sur l'accueil où il est déjà en grand),
puis à droite « Entreprises » et « Se connecter » / « S'inscrire », ou « Mon compte » une fois
connecté (et « Administration » pour les administrateurs).

    header(pages, current="accueil", user=user, is_admin=False)
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

STATIC = Path(__file__).resolve().parent / "static"


def _mode() -> str:
    return "sombre" if getattr(st.context.theme, "type", None) == "dark" else "clair"


def logo_svg() -> str:
    """Le mot « Compass » (SVG d'Emma), clair ou sombre selon le thème, à insérer en HTML."""
    f = STATIC / f"logo-compass-{_mode()}.svg"
    return f.read_text(encoding="utf-8") if f.exists() else "<b>Compass</b>"


def header(pages: dict, current: str, user: dict | None, is_admin: bool = False) -> None:
    """`pages` : nom → st.Page (accueil, recherche, entreprises, compte, admin)."""
    with st.container(key="entete"):
        left, _, right = st.columns([2.2, 3, 4.2], vertical_alignment="center")
        if current != "accueil":
            # lien relatif : marche aussi derrière le proxy d'Onyxia (…/proxy/8501/)
            left.markdown(
                f"<a class='entete-logo' href='./' target='_self'>{logo_svg()}</a>",
                unsafe_allow_html=True,
            )
        with right, st.container(horizontal=True, horizontal_alignment="right", gap="small"):
            if current != "accueil":
                st.page_link(pages["entreprises"], label="Entreprises", icon=":material/apartment:")
            if user is None:
                st.page_link(pages["compte"], label="Se connecter", icon=":material/login:",
                             query_params={"mode": "connexion"})  # fmt: skip
                with st.container(key="entete_inscription"):
                    st.page_link(pages["compte"], label="S'inscrire",
                                 query_params={"mode": "inscription"})  # fmt: skip
            else:
                if is_admin and "admin" in pages:
                    st.page_link(pages["admin"], label="Administration",
                                 icon=":material/admin_panel_settings:")  # fmt: skip
                st.page_link(pages["compte"], label="Mon compte", icon=":material/person:")
