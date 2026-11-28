"""Apparence de l'app (T70) : CSS commun, en-tête de page, chiffres de Mon compte, cartes.

Le thème de base (couleurs, police) est dans .streamlit/config.toml. Ici : ce que le thème
ne sait pas faire. Les blocs stylés sont des `st.container(key=...)` : Streamlit leur donne la
classe CSS `st-key-<clé>`, plus stable que les classes internes.

    inject_css()                         # une fois, dans app/streamlit_app.py
    hero("Radar", "Trouve les entreprises…")
    stat_bar([Stat("4", "candidatures"), Stat("1", "à relancer", alert=True)])
"""

from __future__ import annotations

import base64
import html
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

NAVY = "#1D3557"
NAVY_LIGHT = "#2B4C7E"
BG_CARD = "#FFFFFF"
GREEN = "#2E7D32"
# Texte cliquable dans un tableau (T72) : le nom d'une entreprise ouvre sa fiche.
LINK_STYLE = "color: #1a56db; text-decoration: underline; font-weight: 600"
RED = "#B3261E"

# T93 (essai) : deux jeux de couleurs, choisis selon le thème actif (clair / sombre).
PALETTES = {
    "light": {"card": "#FFFFFF", "muted": "#5B6475", "title": "#111827", "tint": "0.08",
              "shadow": "rgba(16,24,40,.07)", "bg_top": "#EAEFFB", "bg": "#F6F7FB"},
    "dark": {"card": "#161D2E", "muted": "#A3ACC2", "title": "#F1F3F9", "tint": "0.16",
             "shadow": "rgba(0,0,0,.35)", "bg_top": "#151C30", "bg": "#0F1422"},
}  # fmt: skip

_CSS = """
<style>
.stApp {{ background: radial-gradient(1200px 380px at 15% -80px, {bg_top} 0%, {bg} 70%); }}

/* Cartes (blocs avec une clé) : fond, coins arrondis, ombre */
.st-key-carte_recherche, [class*="st-key-etape_"], [class*="st-key-cible_"],
[class*="st-key-espace_"], [class*="st-key-tb_"] {{
    background: {card}; border-radius: 16px !important;
    box-shadow: 0 1px 2px {shadow}, 0 8px 24px {shadow};
}}
[class*="st-key-cible_"]:hover, [class*="st-key-tb_"]:hover {{
    box-shadow: 0 10px 28px {shadow}; transform: translateY(-1px); transition: all .15s;
}}

/* En-tête des pages (T95) : comme l'accueil — titre centré, trait orange, phrase grise */
.page-head {{ text-align: center; margin: .8rem 0 1.5rem 0; }}
.page-head h1 {{ font-size: 2rem; font-weight: 800; color: inherit; margin: 0; padding: 0;
                letter-spacing: -.02em; }}
.page-head h1::after {{ content: ""; display: block; width: 3rem; height: 3px;
                       border-radius: 2px; background: #E4572E; margin: .55rem auto; }}
.page-head p {{ color: {muted}; font-size: 1.1rem; margin: 0; }}
.page-avatar {{ display: inline-flex; width: 3.2rem; height: 3.2rem; border-radius: 50%;
               align-items: center; justify-content: center; font-size: 1.4rem;
               font-weight: 800; background: rgba(59, 91, 219, {tint}); margin-bottom: .4rem; }}
.st-key-page_compte {{ width: 100%; max-width: 64rem; margin: 0 auto; }}

.st-key-carte_recherche {{ position: relative; z-index: 2; }}

/* Chiffres de Mon compte (T95) : une seule carte, séparateurs fins, texte neutre */
.stat-bar {{ display: flex; flex-wrap: wrap; background: {card}; border-radius: 16px;
            box-shadow: 0 1px 2px {shadow}, 0 8px 24px {shadow};
            padding: .9rem 0; margin: .2rem 0 1.1rem 0; }}
.stat {{ flex: 1 1 8rem; text-align: center; padding: .1rem .8rem;
        border-left: 1px solid rgba(128, 128, 128, .25); }}
.stat:first-child {{ border-left: none; }}
.stat .v {{ font-size: 1.6rem; font-weight: 700; color: {title}; line-height: 1.2; }}
.stat .l {{ font-size: .88rem; color: {muted}; }}
.stat.alert .l::before {{ content: ""; display: inline-block; width: .5rem; height: .5rem;
                         border-radius: 50%; background: #E4572E; margin-right: .35rem; }}

/* Titre de section (« Tableau de bord ») */
.radar-section {{ font-size: 1.15rem; font-weight: 750; color: {title}; margin: 1.1rem 0 .5rem 0;
                 display: flex; align-items: center; gap: .5rem; }}
.radar-section::before {{ content: ""; width: 6px; height: 1.2rem; border-radius: 3px;
                         background: linear-gradient(180deg, #3B5BDB, #15AABF); }}

/* Cartes « meilleures cibles » */
.radar-pill {{ display: inline-block; padding: .12rem .55rem; border-radius: 999px;
              font-size: .78rem; font-weight: 600; color: #fff; background: var(--c); }}
.radar-card-title {{ font-weight: 650; font-size: 1.02rem; color: {title}; margin: .35rem 0 .1rem 0;
                    line-height: 1.25; }}
.radar-card-sub {{ font-size: .86rem; color: {muted}; }}

.radar-step-n {{ display: inline-flex; width: 2.2rem; height: 2.2rem; border-radius: 12px;
                align-items: center; justify-content: center; font-weight: 800; color: #fff;
                background: linear-gradient(135deg, #3B5BDB, #15AABF); margin-bottom: .4rem; }}

[data-testid="stTab"] p {{ font-size: 1rem; font-weight: 650; }}

/* T93 : notre barre du haut (app/entete.py), sur la même ligne que le menu « ⋮ » de
   Streamlit : la barre de Streamlit devient transparente (seul le menu reste cliquable) et la
   page remonte, pour que nos liens soient centrés à la hauteur des « ⋮ ». */
header[data-testid="stHeader"] {{ background: transparent; pointer-events: none; }}
header[data-testid="stHeader"] * {{ pointer-events: none; }}
/* Seuls les boutons du menu restent cliquables : la zone de la barre (toute la largeur)
   laisse passer les clics vers nos liens. */
header[data-testid="stHeader"] button, header[data-testid="stHeader"] a,
[data-testid="stMainMenu"], [data-testid="stMainMenu"] * {{ pointer-events: auto; }}
.block-container, [data-testid="stMainBlockContainer"] {{ padding-top: .5rem !important; }}
.st-key-entete {{ min-height: 2.75rem; padding-right: 3.4rem; margin-bottom: .8rem;
                 display: flex; align-items: center; }}
.st-key-entete > div, .st-key-entete [data-testid="stHorizontalBlock"] {{ width: 100%;
    align-items: center; }}
.st-key-entete [data-testid="stElementContainer"],
.st-key-entete [data-testid="stPageLink"] {{ margin: 0 !important; }}
/* Logo = lien vers l'accueil (même session) ; texte remplacé par l'image */
.st-key-entete_logo [data-testid="stPageLink"] {{ position: relative; width: 10rem; }}
.st-key-entete_logo [data-testid="stPageLink"] a {{ width: 10rem; height: 2.4rem;
    padding: 0 !important; }}
.st-key-entete_logo [data-testid="stPageLink"] a * {{ opacity: 0; }}
/* T95 : le logo est dessiné dans la couleur du texte du thème (masque), l'aiguille orange
   par-dessus : visible en clair comme en sombre sans deviner le thème ; les clics passent */
.st-key-entete_logo [data-testid="stPageLink"]::before,
.st-key-entete_logo [data-testid="stPageLink"]::after {{
    content: ""; position: absolute; left: 0; top: 0; width: 10rem; height: 2.4rem;
    pointer-events: none; }}
.st-key-entete_logo [data-testid="stPageLink"]::before {{
    background-color: currentColor;
    -webkit-mask: url("{logo_texte}") left center / contain no-repeat;
    mask: url("{logo_texte}") left center / contain no-repeat; }}
.st-key-entete_logo [data-testid="stPageLink"]::after {{
    background: url("{logo_aiguille}") left center / contain no-repeat; }}
.st-key-entete [data-testid="stPageLink"] a {{ border-radius: 999px; padding: .25rem .8rem; }}
.st-key-entete_inscription [data-testid="stPageLink"] a {{
    background: linear-gradient(135deg, #3B5BDB, #15AABF); }}
.st-key-entete_inscription [data-testid="stPageLink"] a p {{ color: #fff !important;
    font-weight: 700; }}

/* T96 : indicateur de chargement de Streamlit (pictogrammes de sport) → boussole qui tourne,
   dans le même gris (couleur du texte à 60 %). Les pictogrammes sont seulement masqués. */
[data-testid="stStatusWidgetRunningIcon"] {{ position: relative; }}
[data-testid="stStatusWidgetRunningIcon"] > * {{ opacity: 0 !important; }}
[data-testid="stStatusWidgetRunningIcon"]::before {{
    content: ""; position: absolute; inset: 0; background-color: currentColor; opacity: .6;
    -webkit-mask: url("{boussole}") center / contain no-repeat;
    mask: url("{boussole}") center / contain no-repeat;
    animation: boussole-tourne 1.1s linear infinite; }}
@keyframes boussole-tourne {{ to {{ transform: rotate(360deg); }} }}

/* T93 : page d'accueil — logo en grand, slogan à côté, phrase, recherche centrée */
.accueil-head {{ display: flex; align-items: center; justify-content: center; gap: 1.6rem;
                flex-wrap: wrap; margin: 2.2rem 0 .4rem 0; }}
.accueil-logo svg {{ height: 7rem; width: auto; display: block; }}
.accueil-slogan {{ font-size: 1.35rem; font-style: italic; font-weight: 600; color: {muted};
                  border-left: 3px solid #E4572E; padding-left: 1rem; max-width: 16rem;
                  line-height: 1.3; }}
.accueil-pitch {{ text-align: center; font-size: 1.15rem; color: {title};
                 margin: .4rem 0 1.8rem 0; }}
.st-key-carte_recherche_accueil {{ background: {card}; border-radius: 18px !important;
    box-shadow: 0 1px 2px {shadow}, 0 12px 32px {shadow}; padding: .6rem .4rem; }}
.st-key-lien_entreprise {{ display: flex; align-items: center; }}
.st-key-lien_entreprise [data-testid="stPageLink"] {{ margin: .6rem auto 0 auto; }}
.st-key-lien_entreprise [data-testid="stPageLink"] p {{ text-decoration: underline; }}

/* T93 : lien vers l'autre page (connexion ↔ inscription), centré et souligné */
.st-key-lien_autre_page {{ display: flex; align-items: center; }}
.st-key-lien_autre_page [data-testid="stPageLink"] {{ margin: .5rem auto 0 auto; }}
.st-key-lien_autre_page [data-testid="stPageLink"] p {{ text-decoration: underline; }}

/* T93 : titre du bloc de recherche (page de résultats) */
.radar-block-title {{ font-size: 1.1rem; font-weight: 750; color: {title}; margin-bottom: .2rem; }}

/* Logo « Compass » de la barre du haut, un peu plus grand que la taille « large » de Streamlit */
img[data-testid="stLogo"], [data-testid="stHeaderLogo"] img {{
    height: 2.4rem !important; max-height: 2.4rem !important; width: auto !important; }}

/* En-tête des fiches (T89, @celia) : initiale, nom, pastilles — couleurs du thème (T93) */
.fiche-head {{ display: flex; align-items: center; gap: .9rem; margin-bottom: .55rem; }}
.fiche-avatar {{ width: 3.1rem; height: 3.1rem; border-radius: 14px; flex: none;
                display: flex; align-items: center; justify-content: center;
                font-size: 1.4rem; font-weight: 700; color: #fff;
                background: linear-gradient(135deg, #1B2A6B, #3B5BDB); }}
.fiche-title {{ font-size: 1.35rem; font-weight: 700; color: {title}; line-height: 1.25; }}
.fiche-sub {{ font-size: .88rem; color: {muted}; }}
.fiche-chips {{ display: flex; flex-wrap: wrap; gap: .4rem; margin-bottom: .6rem; }}
.fiche-chips .radar-pill {{ font-size: .8rem; }}
.radar-chip {{ display: inline-block; padding: .12rem .6rem; border-radius: 999px;
              font-size: .8rem; color: {title}; background: rgba(59, 91, 219, {tint}); }}
</style>
"""

# Logo « Compass » (SVG d'Emma) découpé en deux images pour la barre du haut (T95) : tout sauf
# l'aiguille orange (utilisé comme masque, coloré par le thème), et l'aiguille orange seule.
_LOGO_FILE = Path(__file__).resolve().parent / "static" / "logo-compass-clair.svg"
LOGO_NAVY, LOGO_ORANGE = "#14213D", "#E4572E"


def _data_uri(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def _logo_layers() -> dict[str, str]:
    if not _LOGO_FILE.exists():
        return {"logo_texte": "", "logo_aiguille": ""}
    svg = _LOGO_FILE.read_text(encoding="utf-8")
    return {
        "logo_texte": _data_uri(svg.replace(LOGO_ORANGE, "none")),
        "logo_aiguille": _data_uri(svg.replace(LOGO_NAVY, "none")),
    }


LOGO_LAYERS = _logo_layers()
# Boussole de l'indicateur de chargement (T96) : anneau et aiguille, dont la moitié sud est plus
# pâle pour qu'on la voie tourner. Sert de masque : seule la transparence compte.
LOADING_COMPASS = _data_uri(
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 60'>"
    "<circle cx='30' cy='30' r='26' fill='none' stroke='#000' stroke-width='6'/>"
    "<path d='M30 9 L37 30 L23 30 Z'/><path d='M30 51 L37 30 L23 30 Z' fill-opacity='.4'/></svg>"
)
CSS_IMAGES = {**LOGO_LAYERS, "boussole": LOADING_COMPASS}


def _palette() -> dict[str, str]:
    """Couleurs du thème actif (clair par défaut si Streamlit ne le dit pas)."""
    try:
        mode = st.context.theme.type or "light"
    except AttributeError:
        mode = "light"
    return PALETTES.get(mode, PALETTES["light"])


CSS = _CSS.format(
    **PALETTES["light"], **CSS_IMAGES
)  # version claire, pour qui l'importe directement


def inject_css() -> None:
    st.markdown(_CSS.format(**_palette(), **CSS_IMAGES), unsafe_allow_html=True)


def hero(title: str, tagline: str) -> None:
    """En-tête d'une page (T95) : titre centré et phrase, dans le style de l'accueil."""
    st.markdown(
        f"<div class='page-head'><h1>{html.escape(title)}</h1><p>{html.escape(tagline)}</p></div>",
        unsafe_allow_html=True,
    )


def profile_header(username: str, tagline: str) -> None:
    """En-tête de Mon compte : initiale dans un rond, « Bonjour … » et une phrase."""
    initial = html.escape(username[:1].upper() or "?")
    st.markdown(
        f"<div class='page-head'><span class='page-avatar'>{initial}</span>"
        f"<h1>Bonjour {html.escape(username)}</h1><p>{html.escape(tagline)}</p></div>",
        unsafe_allow_html=True,
    )


def chip(text: str) -> str:
    """Pastille grise (HTML) pour une information neutre."""
    return f"<span class='radar-chip'>{html.escape(text)}</span>"


def fiche_header(title: str, subtitle: str, chips: list[str]) -> None:
    """En-tête d'une fiche (T89). `chips` : HTML déjà échappé (chip ou pill)."""
    initial = html.escape(next((c for c in title if c.isalnum()), "?").upper())
    st.markdown(
        f"<div class='fiche-head'><span class='fiche-avatar'>{initial}</span><div>"
        f"<div class='fiche-title'>{html.escape(title)}</div>"
        f"<div class='fiche-sub'>{html.escape(subtitle)}</div></div></div>"
        f"<div class='fiche-chips'>{''.join(chips)}</div>",
        unsafe_allow_html=True,
    )


@dataclass(frozen=True)
class Stat:
    value: str
    label: str
    alert: bool = False  # point orange : quelque chose à faire


def stat_bar(stats: list[Stat]) -> None:
    """Les chiffres d'une page, dans une seule carte."""
    cells = "".join(
        f"<div class='stat{' alert' if s.alert else ''}'>"
        f"<div class='v'>{html.escape(s.value)}</div>"
        f"<div class='l'>{html.escape(s.label)}</div></div>"
        for s in stats
    )
    st.markdown(f"<div class='stat-bar'>{cells}</div>", unsafe_allow_html=True)


def pill(text: str, color: str) -> str:
    """Pastille colorée (HTML) pour un libellé court."""
    return f"<span class='radar-pill' style='--c:{color}'>{html.escape(text)}</span>"


def fmt_int(n: int) -> str:
    """3755 → « 3 755 »."""
    return f"{n:,}".replace(",", " ")
