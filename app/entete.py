"""T93 (essai, branche emma/interface-riche) — Barre du haut de Compass.

Streamlit place sa navigation à gauche ; on la masque (`position="hidden"`) et on dessine notre
barre : le logo à gauche (lien vers l'accueil, sauf sur l'accueil où il est déjà en grand),
puis à droite « Entreprises » et « Se connecter » / « S'inscrire », ou « Mon compte » une fois
connecté (et « Administration » pour les administrateurs).

    header(pages, current="accueil", user=user, is_admin=False)
    page("recherche"); go("recherche")      # dans une page : lien, rappel de bouton
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


PAGES_KEY = "_pages"
GO_PAGE_KEY = "_go_page"  # même clé que app/compte.py


def page(name: str):
    """La page `name` (accueil, recherche, entreprises, compte, connexion, inscription…) de la
    session en cours, enregistrée par app/streamlit_app.py."""
    return st.session_state[PAGES_KEY][name]


def go(name: str) -> None:
    """À utiliser en rappel de bouton : ouvre la page `name` au passage suivant."""
    st.session_state[GO_PAGE_KEY] = name


def header(pages: dict, current: str, user: dict | None, is_admin: bool = False) -> None:
    """`pages` : nom → st.Page (accueil, recherche, entreprises, compte, admin)."""
    with st.container(key="entete"):
        left, _, right = st.columns([2.2, 3, 4.2], vertical_alignment="center")
        if current != "accueil":
            # Le logo est un lien Streamlit (même session : on reste connecté), dont le texte
            # est remplacé par l'image en CSS (app/static/, servi par Streamlit).
            with left, st.container(key=f"entete_logo_{_mode()}"):
                st.page_link(pages["accueil"], label="Compass")
        with right, st.container(horizontal=True, horizontal_alignment="right", gap="small"):
            if current != "accueil":
                st.page_link(pages["entreprises"], label="Entreprises", icon=":material/apartment:")
            if user is None:
                st.page_link(pages["connexion"], label="Se connecter", icon=":material/login:")
                with st.container(key="entete_inscription"):
                    st.page_link(pages["inscription"], label="S'inscrire")
            else:
                if is_admin and "admin" in pages:
                    st.page_link(pages["admin"], label="Administration",
                                 icon=":material/admin_panel_settings:")  # fmt: skip
                st.page_link(pages["compte"], label="Mon compte", icon=":material/person:")
