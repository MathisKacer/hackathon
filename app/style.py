"""Apparence de l'app (T70) : CSS commun, bandeau d'en-tête, tuiles de chiffres, cartes.

Le thème de base (couleurs, police) est dans .streamlit/config.toml. Ici : ce que le thème
ne sait pas faire. Les blocs stylés sont des `st.container(key=...)` : Streamlit leur donne la
classe CSS `st-key-<clé>`, plus stable que les classes internes.

    inject_css()                         # une fois, dans app/streamlit_app.py
    hero("Radar", "Trouve les entreprises…")
    kpi_tiles([Tile("3 755", "entreprises à contacter", ORANGE, "domain"), …])
"""

from __future__ import annotations

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

/* Bandeau d'en-tête : dégradé indigo → bleu → turquoise, radar animé à droite */
.radar-hero {{
    background: linear-gradient(115deg, #1B2A6B 0%, #3B5BDB 55%, #15AABF 100%);
    color: #fff; border-radius: 22px; padding: 1.9rem 2rem 3.4rem 2rem;
    margin-bottom: -2.2rem; position: relative; overflow: hidden;
}}
.radar-hero h1 {{ color: #fff; font-size: 2.3rem; font-weight: 800; margin: 0 0 .35rem 0;
                 padding: 0; letter-spacing: -.02em; }}
.radar-hero p {{ color: rgba(255,255,255,.9); font-size: 1.05rem; margin: 0; max-width: 40rem; }}
.radar-hero .badges {{ margin-top: .8rem; display: flex; gap: .5rem; flex-wrap: wrap; }}
.radar-hero .badges span {{ background: rgba(255,255,255,.16); border: 1px solid
    rgba(255,255,255,.25); border-radius: 999px; padding: .2rem .7rem; font-size: .82rem; }}
.radar-hero svg.compass {{ position: absolute; right: 2rem; top: 50%; width: 170px;
    height: 170px; transform: translateY(-50%); opacity: .95;
    filter: drop-shadow(0 6px 18px rgba(0,0,0,.25)); }}
@media (max-width: 900px) {{ .radar-hero svg.compass {{ display: none; }} }}
.radar-hero.compact {{ padding: 1.3rem 1.7rem; margin-bottom: 1rem; }}
.radar-hero.compact h1 {{ font-size: 1.7rem; }}
.radar-hero.compact svg.compass {{ width: 96px; height: 96px; right: 1.5rem; }}

.st-key-carte_recherche {{ position: relative; z-index: 2; }}

/* Tuiles de chiffres : icône dans une pastille teintée, grand chiffre */
.radar-tiles {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
               gap: .9rem; margin: .6rem 0 1.1rem 0; }}
.radar-tile {{ background: {card}; border-radius: 16px; padding: 1rem 1.1rem;
              display: flex; gap: .85rem; align-items: center;
              box-shadow: 0 1px 2px {shadow}, 0 8px 22px {shadow};
              border-top: 4px solid var(--c); }}
.radar-tile .i {{ flex: none; width: 2.6rem; height: 2.6rem; border-radius: 12px;
                 display: flex; align-items: center; justify-content: center;
                 font-size: 1.35rem; background: color-mix(in srgb, var(--c) calc({tint} * 100%),
                 transparent); }}
.radar-tile .v {{ font-size: 1.75rem; font-weight: 800; color: var(--c); line-height: 1.05; }}
.radar-tile .l {{ font-size: .86rem; color: {muted}; margin-top: .15rem; }}

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

.radar-hero .who {{ display: flex; align-items: center; gap: 1rem; }}
.radar-avatar {{ width: 3.4rem; height: 3.4rem; border-radius: 50%; flex: none;
                display: flex; align-items: center; justify-content: center;
                font-size: 1.5rem; font-weight: 800; color: #3B5BDB; background: #fff; }}

[data-testid="stTab"] p {{ font-size: 1rem; font-weight: 650; }}

/* T93 : notre barre du haut (app/entete.py), posée sur la ligne de la barre de Streamlit
   (celle des « ⋮ ») : fixe en haut, en laissant la place du menu à droite. */
.st-key-entete {{ position: fixed; top: 0; left: 0; right: 3.6rem; height: 3.75rem;
                 z-index: 999991; padding: 0 1.2rem; display: flex; align-items: center; }}
.st-key-entete > div {{ width: 100%; }}
/* Logo = lien vers l'accueil (même session) ; texte remplacé par l'image */
[class*="st-key-entete_logo_"] [data-testid="stPageLink"] a {{
    width: 10rem; height: 2.4rem; background: center left / contain no-repeat;
    padding: 0 !important; }}
[class*="st-key-entete_logo_"] [data-testid="stPageLink"] a * {{ opacity: 0; }}
.st-key-entete_logo_clair [data-testid="stPageLink"] a {{
    background-image: url("app/static/logo-compass-clair.svg"); }}
.st-key-entete_logo_sombre [data-testid="stPageLink"] a {{
    background-image: url("app/static/logo-compass-sombre.svg"); }}
.st-key-entete [data-testid="stPageLink"] a {{ border-radius: 999px; padding: .25rem .8rem; }}
.st-key-entete_inscription [data-testid="stPageLink"] a {{
    background: linear-gradient(135deg, #3B5BDB, #15AABF); }}
.st-key-entete_inscription [data-testid="stPageLink"] a p {{ color: #fff !important;
    font-weight: 700; }}

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

# Boussole du bandeau (T93) : le C-boussole d'Emma en version claire (blanc + aiguille orange),
# lisible sur le dégradé ; lue une fois dans app/static/.
_ICON_FILE = Path(__file__).resolve().parent / "static" / "icone-compass-sombre.svg"
COMPASS_SVG = (
    _ICON_FILE.read_text(encoding="utf-8").replace("<svg ", "<svg class='compass' ", 1)
    if _ICON_FILE.exists()
    else ""
)


def _palette() -> dict[str, str]:
    """Couleurs du thème actif (clair par défaut si Streamlit ne le dit pas)."""
    try:
        mode = st.context.theme.type or "light"
    except AttributeError:
        mode = "light"
    return PALETTES.get(mode, PALETTES["light"])


CSS = _CSS.format(**PALETTES["light"])  # version claire, pour qui l'importe directement


def inject_css() -> None:
    st.markdown(_CSS.format(**_palette()), unsafe_allow_html=True)


def hero(title: str, tagline: str, compact: bool = False, badges: list[str] = ()) -> None:
    """Bandeau d'en-tête coloré (titre + accroche + radar animé, pastilles facultatives)."""
    cls = "radar-hero compact" if compact else "radar-hero"
    tags = "".join(f"<span>{html.escape(b)}</span>" for b in badges)
    st.markdown(
        f"<div class='{cls}'>{COMPASS_SVG}<h1>{html.escape(title)}</h1>"
        f"<p>{html.escape(tagline)}</p>"
        + (f"<div class='badges'>{tags}</div>" if tags else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def profile_header(username: str, tagline: str) -> None:
    """Bandeau de Mon espace : initiale dans un rond, « Bonjour … » et une phrase."""
    initial = html.escape(username[:1].upper() or "?")
    st.markdown(
        f"<div class='radar-hero compact'><div class='who'><span class='radar-avatar'>{initial}"
        f"</span><div><h1>Bonjour {html.escape(username)}</h1><p>{html.escape(tagline)}</p>"
        "</div></div></div>",
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
class Tile:
    value: str
    label: str
    color: str
    icon: str = ""  # T93 : emoji dans une pastille teintée


def kpi_tiles(tiles: list[Tile]) -> None:
    """Rangée de tuiles : un grand chiffre coloré et un libellé."""
    cells = "".join(
        f"<div class='radar-tile' style='--c:{t.color}'>"
        + (f"<div class='i'>{html.escape(t.icon)}</div>" if t.icon else "")
        + f"<div><div class='v'>{html.escape(t.value)}</div>"
        f"<div class='l'>{html.escape(t.label)}</div></div></div>"
        for t in tiles
    )
    st.markdown(f"<div class='radar-tiles'>{cells}</div>", unsafe_allow_html=True)


def pill(text: str, color: str) -> str:
    """Pastille colorée (HTML) pour un libellé court."""
    return f"<span class='radar-pill' style='--c:{color}'>{html.escape(text)}</span>"


def fmt_int(n: int) -> str:
    """3755 → « 3 755 »."""
    return f"{n:,}".replace(",", " ")
