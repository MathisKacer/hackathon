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

import streamlit as st

NAVY = "#1D3557"
NAVY_LIGHT = "#2B4C7E"
BG_CARD = "#FFFFFF"
GREEN = "#2E7D32"
RED = "#B3261E"

CSS = f"""
<style>
/* Fond très légèrement teinté et respiration générale */
.stApp {{ background: linear-gradient(180deg, #F4F6FA 0%, #FAFAF7 320px); }}
.block-container {{ padding-top: 1.2rem; }}

/* Nos cartes (blocs avec une clé) : fond blanc, coins arrondis, ombre légère.
   Les clés `st.container(key=...)` donnent la classe `st-key-<clé>`, stable d'une version à
   l'autre de Streamlit (contrairement aux identifiants internes). */
.st-key-carte_recherche, [class*="st-key-etape_"], [class*="st-key-cible_"] {{
    background: {BG_CARD};
    border-radius: 14px !important;
    box-shadow: 0 1px 2px rgba(16, 24, 40, .04), 0 4px 14px rgba(16, 24, 40, .06);
}}
[class*="st-key-cible_"]:hover {{ box-shadow: 0 6px 20px rgba(16, 24, 40, .10); }}

/* Bandeau d'en-tête */
.radar-hero {{
    background: linear-gradient(120deg, {NAVY} 0%, {NAVY_LIGHT} 60%, #3A6EA5 100%);
    color: #fff; border-radius: 18px; padding: 1.6rem 1.8rem 3.2rem 1.8rem;
    margin-bottom: -2.2rem;  /* la carte de recherche vient se poser sur le bandeau */
    position: relative; overflow: hidden;
}}
.radar-hero::after {{  /* cercles décoratifs discrets, évocation d'un radar */
    content: ""; position: absolute; right: -60px; top: -60px; width: 260px; height: 260px;
    border-radius: 50%; border: 2px solid rgba(255,255,255,.12);
    box-shadow: 0 0 0 40px rgba(255,255,255,.04), 0 0 0 80px rgba(255,255,255,.03);
}}
.radar-hero h1 {{ color: #fff; font-size: 2.1rem; font-weight: 700; margin: 0 0 .3rem 0;
                 padding: 0; letter-spacing: -.01em; }}
.radar-hero p {{ color: rgba(255,255,255,.86); font-size: 1.02rem; margin: 0; max-width: 46rem; }}
.radar-hero.compact {{ padding: 1.2rem 1.6rem; margin-bottom: 1rem; }}
.radar-hero.compact h1 {{ font-size: 1.6rem; }}

/* Carte de recherche posée sur le bandeau */
.st-key-carte_recherche {{ position: relative; z-index: 2; }}

/* Tuiles de chiffres */
.radar-tiles {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
               gap: .8rem; margin: .4rem 0 1rem 0; }}
.radar-tile {{ background: {BG_CARD}; border-radius: 14px; padding: .9rem 1rem;
              border-left: 5px solid var(--c); box-shadow: 0 2px 10px rgba(16,24,40,.05); }}
.radar-tile .v {{ font-size: 1.7rem; font-weight: 700; color: var(--c); line-height: 1.1; }}
.radar-tile .l {{ font-size: .88rem; color: #4B5563; margin-top: .15rem; }}

/* Cartes « meilleures cibles » */
.radar-pill {{ display: inline-block; padding: .12rem .55rem; border-radius: 999px;
              font-size: .78rem; font-weight: 600; color: #fff; background: var(--c); }}
.radar-card-title {{ font-weight: 650; font-size: 1.02rem; color: #111827; margin: .35rem 0 .1rem 0;
                    line-height: 1.25; }}
.radar-card-sub {{ font-size: .86rem; color: #6B7280; }}

/* Étapes « Comment ça marche » */
.radar-step-n {{ display: inline-flex; width: 2rem; height: 2rem; border-radius: 50%;
                align-items: center; justify-content: center; font-weight: 700;
                background: {NAVY}; color: #fff; margin-bottom: .4rem; }}

/* Onglets un peu plus marqués */
[data-testid="stTab"] p {{ font-size: 1rem; font-weight: 600; }}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title: str, tagline: str, compact: bool = False) -> None:
    """Bandeau d'en-tête coloré (titre + accroche)."""
    cls = "radar-hero compact" if compact else "radar-hero"
    st.markdown(
        f"<div class='{cls}'><h1>{html.escape(title)}</h1><p>{html.escape(tagline)}</p></div>",
        unsafe_allow_html=True,
    )


@dataclass(frozen=True)
class Tile:
    value: str
    label: str
    color: str


def kpi_tiles(tiles: list[Tile]) -> None:
    """Rangée de tuiles : un grand chiffre coloré et un libellé."""
    cells = "".join(
        f"<div class='radar-tile' style='--c:{t.color}'><div class='v'>{html.escape(t.value)}</div>"
        f"<div class='l'>{html.escape(t.label)}</div></div>"
        for t in tiles
    )
    st.markdown(f"<div class='radar-tiles'>{cells}</div>", unsafe_allow_html=True)


def pill(text: str, color: str) -> str:
    """Pastille colorée (HTML) pour un libellé court."""
    return f"<span class='radar-pill' style='--c:{color}'>{html.escape(text)}</span>"


def fmt_int(n: int) -> str:
    """3755 → « 3 755 »."""
    return f"{n:,}".replace(",", " ")
