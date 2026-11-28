"""T93 (essai, branche emma/interface-riche) — Tableau de bord de la recherche, page Explorer.

Quatre petits graphiques sur les candidatures spontanées de la recherche en cours :
priorité, correspondance avec le CV (si des compétences sont indiquées), secteurs, tailles.
Barres horizontales fines, une seule teinte par graphique (ou les couleurs déjà utilisées dans
la liste : paliers de priorité, paliers de correspondance), info-bulle au survol, thème
Streamlit (s'adapte au mode clair / sombre).

    dashboard(spontaneous)      # après les tuiles de chiffres
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from radar.competences import MATCH_COLORS, MATCH_TIERS
from radar.filters import SECTIONS, TAILLES
from radar.paliers import TIERS, tier_color

BAR = "#3A6EA5"  # teinte unique des graphiques sans couleur de sens
_SIZE_OF = {code: label for label, codes in TAILLES.items() for code in codes}


def _bars(df: pd.DataFrame, colors: list[str] | None = None, height: int = 170) -> alt.Chart:
    """Barres horizontales : `libelle` (ordre du tableau), `n` ; couleur fixe ou par barre."""
    order = df["libelle"].tolist()
    total = max(int(df["n"].sum()), 1)
    df = df.assign(part=df["n"] / total)
    color = (
        alt.Color("libelle:N", scale=alt.Scale(domain=order, range=colors), legend=None)
        if colors
        else alt.value(BAR)
    )
    return (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=4, height={"band": 0.7})
        .encode(
            y=alt.Y("libelle:N", sort=order, title=None, axis=alt.Axis(labelLimit=190)),
            x=alt.X("n:Q", title=None, axis=alt.Axis(grid=False, tickCount=3, format="d")),
            color=color,
            tooltip=[
                alt.Tooltip("libelle:N", title=""),
                alt.Tooltip("n:Q", title="Entreprises", format=",d"),
                alt.Tooltip("part:Q", title="Part", format=".0%"),
            ],
        )
        .properties(height=height)
    )


def _counts(values: pd.Series, order: list[str] | None = None, top: int | None = None):
    c = values.dropna().value_counts()
    if order is not None:
        c = c.reindex(order).fillna(0).astype(int)
        c = c[c > 0]
    elif top is not None and len(c) > top:
        c = pd.concat([c.head(top), pd.Series({"Autres secteurs": int(c.iloc[top:].sum())})])
    return pd.DataFrame({"libelle": c.index.astype(str), "n": c.to_numpy()})


def _card(key: str, title: str, chart: alt.Chart | None, empty: str) -> None:
    with st.container(border=True, key=f"tb_{key}"):
        st.markdown(f"**{title}**")
        if chart is None:
            st.caption(empty)
        else:
            st.altair_chart(chart, width="stretch", theme="streamlit")


def dashboard(spontaneous: pd.DataFrame) -> None:
    """Quatre graphiques ; rien si la recherche ne donne aucune candidature spontanée."""
    if spontaneous.empty:
        return
    st.markdown("<div class='radar-section'>Tableau de bord</div>", unsafe_allow_html=True)

    # 1. Priorité (couleurs des paliers, du plus foncé au gris, comme la liste)
    labels = {t.rank: t.label for t in TIERS}
    prio = _counts(spontaneous.get("palier", pd.Series(dtype=float)).map(labels),
                   order=[t.label for t in TIERS])  # fmt: skip
    prio_chart = _bars(prio, [tier_color(t.rank) for t in TIERS if t.label in set(prio.libelle)])

    # 2. Correspondance avec le CV (paliers de mots)
    match_order = [label for _, label in MATCH_TIERS]
    if (
        "correspondance_palier" in spontaneous
        and spontaneous["correspondance_palier"].notna().any()
    ):
        m = _counts(spontaneous["correspondance_palier"], order=match_order)
        match_chart = _bars(m, [MATCH_COLORS[x] for x in m.libelle])
    else:
        match_chart = None

    # 3. Secteurs (sections NAF), 7 premiers + « Autres secteurs »
    sect = spontaneous.get("naf_section", pd.Series(dtype=str)).map(SECTIONS)
    sect_chart = _bars(_counts(sect, top=7), height=220) if sect.notna().any() else None

    # 4. Taille des sites (classes du filtre « Taille »)
    size = spontaneous.get("tranche_effectif", pd.Series(dtype=str)).astype("string").map(_SIZE_OF)
    size_chart = _bars(_counts(size, order=list(TAILLES))) if size.notna().any() else None

    c1, c2 = st.columns(2)
    with c1:
        _card("priorite", "Par priorité", prio_chart, "Pas de priorité calculée.")
    with c2:
        _card(
            "correspondance",
            "Correspondance avec ton CV",
            match_chart,
            "Indique tes compétences (Filtres › Ton CV) pour voir à quel point tu corresponds "
            "aux entreprises de ta recherche.",
        )
    c3, c4 = st.columns(2)
    with c3:
        _card("secteurs", "Par secteur", sect_chart, "Secteur inconnu.")
    with c4:
        _card("tailles", "Par taille du site", size_chart, "Taille inconnue.")
