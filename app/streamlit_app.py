"""Application Radar (Streamlit).

Lancer : uv run streamlit run app/streamlit_app.py

Carte à deux couches (D8) :
- 🔵 Offres réelles (T39) : offres actuelles filtrées sur le domaine et le contrat visé ;
- 🟠 Candidature spontanée (T40, à venir) : entreprises sans offre correspondante.
"""

from __future__ import annotations

import html
import math

import folium
import pandas as pd
import streamlit as st
from compte import account_sidebar  # app/compte.py (T48)
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from radar.process.quick_filter import load_raw_offers, prepare_offers

BLUE = "#1f6feb"
ORANGE = "#e8590c"
FRANCE_CENTER = (46.6, 2.4)
MAX_OFFERS_IN_POPUP = 25

st.set_page_config(page_title="Radar", page_icon="📡", layout="wide")


@st.cache_data(show_spinner="Chargement des offres…")
def get_offers() -> pd.DataFrame:
    return prepare_offers(load_raw_offers())


def filter_offers(
    df: pd.DataFrame,
    regions: list[str],
    contrat: str,
    only_data: bool,
    max_age: int,
    query: str,
) -> pd.DataFrame:
    out = df
    if only_data:
        out = out[out["is_data"]]
    if regions:
        out = out[out["region_requete"].isin(regions)]
    if contrat != "Tous":
        out = out[out["contrat"] == contrat.lower()]
    out = out[out["age_jours"].fillna(0) <= max_age]
    if query:
        q = query.lower()
        hay = (
            out["titre"].fillna("").str.lower() + " " + out["entreprise_nom"].fillna("").str.lower()
        )
        out = out[hay.str.contains(q, regex=False)]
    return out


def _popup_html(group: pd.DataFrame) -> str:
    """Liste des offres d'un même lieu (texte échappé : les titres viennent d'Internet)."""
    place = html.escape(str(group["commune"].iloc[0] or ""))
    n = len(group)
    items = []
    for _, r in group.sort_values("age_jours").head(MAX_OFFERS_IN_POPUP).iterrows():
        title = html.escape(str(r["titre"] or "Sans titre"))
        company = html.escape(str(r["entreprise_nom"] or "Entreprise non précisée"))
        url = html.escape(str(r["url"] or ""), quote=True)
        age = "" if pd.isna(r["age_jours"]) else f" · il y a {int(r['age_jours'])} j"
        badge = {"stage": "🎓 Stage", "alternance": "🔁 Alternance"}.get(r["contrat"], "💼 Emploi")
        link = f'<a href="{url}" target="_blank" rel="noopener">{title}</a>' if url else title
        items.append(
            f"<li style='margin-bottom:6px'>{link}<br>"
            f"<span style='color:#555'>{company} · {badge}{age}</span></li>"
        )
    more = (
        f"<p style='color:#555'>… et {n - MAX_OFFERS_IN_POPUP} autres</p>"
        if n > MAX_OFFERS_IN_POPUP
        else ""
    )
    return (
        f"<div style='font-family:sans-serif;font-size:13px;max-height:280px;overflow-y:auto'>"
        f"<b>{place}</b> — {n} offre{'s' if n > 1 else ''}"
        f"<ul style='padding-left:16px;margin-top:6px'>{''.join(items)}</ul>{more}</div>"
    )


def build_map(offers: pd.DataFrame) -> folium.Map:
    if offers.empty:
        center, zoom = FRANCE_CENTER, 6
    else:
        center, zoom = (offers["lat"].median(), offers["lon"].median()), 7
    m = folium.Map(location=center, zoom_start=zoom, tiles="OpenStreetMap", control_scale=True)

    layer = folium.FeatureGroup(name="🔵 Offres réelles", show=True)
    cluster = MarkerCluster(options={"showCoverageOnHover": False}).add_to(layer)
    # Un point par lieu : les offres Adzuna sont souvent placées au centre de la commune.
    grouped = offers.assign(_lat=offers["lat"].round(4), _lon=offers["lon"].round(4))
    for (lat, lon), group in grouped.groupby(["_lat", "_lon"]):
        n = len(group)
        folium.CircleMarker(
            location=(lat, lon),
            radius=5 + 3 * math.log1p(n),
            color=BLUE,
            weight=1,
            fill=True,
            fill_color=BLUE,
            fill_opacity=0.7,
            tooltip=f"{group['commune'].iloc[0] or ''} — {n} offre{'s' if n > 1 else ''}",
            popup=folium.Popup(_popup_html(group), max_width=380),
        ).add_to(cluster)
    layer.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


# ---------------------------------------------------------------- interface
st.title("📡 Radar")
st.caption(
    "Les offres qui existent… et les entreprises qui pourraient te répondre sans en avoir publié."
)

offers = get_offers()
if offers.empty:
    st.info(
        "Aucune offre trouvée dans `data/raw/offres_raw/`. "
        "Lance `uv run python scripts/collect_adzuna.py` ou récupère le parquet depuis S3."
    )
    st.stop()

DOMAINES = ["Data"]
CONTRATS = ["Tous", "Stage", "Alternance", "Emploi"]
all_regions = sorted(offers["region_requete"].dropna().unique())

# Réglages enregistrés dans le profil quand on est connecté (T48) : clé du widget → options
# permises (None = libre). Ajouter ici la clé de tout nouveau réglage (T40, T41, T42…).
PROFILE_KEYS = {
    "domaine": DOMAINES,
    "contrat": CONTRATS,
    "regions": all_regions,
    "query": None,
    "max_age": list(range(7, 61, 7)) + [60],
    "only_data": [True, False],
}
# Valeurs par défaut posées dans session_state (et non via value=) pour qu'un profil chargé
# puisse les remplacer sans avertissement de Streamlit.
st.session_state.setdefault("max_age", 60)
st.session_state.setdefault("only_data", True)

with st.sidebar:
    account_sidebar(PROFILE_KEYS)
    st.divider()
    st.header("Ta recherche")
    st.selectbox("Domaine", DOMAINES, key="domaine", help="D'autres domaines arriveront avec T6.")
    contrat = st.radio("Contrat visé", CONTRATS, horizontal=True, key="contrat")
    regions = st.multiselect(
        "Régions", all_regions, placeholder="Toutes les régions collectées", key="regions"
    )
    query = st.text_input(
        "Mot-clé (titre ou entreprise)", placeholder="ex. python, Arkéa…", key="query"
    )
    max_age = st.slider("Publiées il y a moins de (jours)", 7, 60, step=7, key="max_age")
    only_data = st.toggle(
        "Seulement les offres data",
        key="only_data",
        help="Filtre v0 sur le titre, en attendant le classifieur T13. "
        "Désactivé : toutes les offres renvoyées par la recherche « data » d'Adzuna (bruitées).",
    )
    st.divider()
    st.markdown(
        f"<span style='color:{BLUE}'>●</span> **Offres réelles** : annonces en ligne (Adzuna)<br>"
        f"<span style='color:{ORANGE}'>●</span> **Candidature spontanée** : *bientôt* "
        "(entreprises sans offre mais susceptibles de répondre)",
        unsafe_allow_html=True,
    )

view = filter_offers(offers, regions, contrat, only_data, max_age, query.strip())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Offres", f"{len(view):,}".replace(",", " "))
c2.metric("Entreprises", f"{view['entreprise_nom'].nunique():,}".replace(",", " "))
c3.metric("Stages", int((view["contrat"] == "stage").sum()))
c4.metric("Alternances", int((view["contrat"] == "alternance").sum()))

if view.empty:
    st.warning("Aucune offre ne correspond à ces filtres.")
else:
    st_folium(build_map(view), height=620, use_container_width=True, returned_objects=[])

    st.subheader("Liste des offres")
    table = view.sort_values("age_jours")[
        ["titre", "entreprise_nom", "commune", "contrat", "age_jours", "url"]
    ].rename(
        columns={
            "titre": "Offre",
            "entreprise_nom": "Entreprise",
            "commune": "Lieu",
            "contrat": "Contrat",
            "age_jours": "Publiée il y a (j)",
            "url": "Annonce",
        }
    )
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={"Annonce": st.column_config.LinkColumn("Annonce", display_text="Voir")},
    )

st.caption(
    f"Source : Adzuna, collecte du {offers['date_collecte'].max()[:10]}. "
    "Régions collectées : " + ", ".join(sorted(offers["region_requete"].dropna().unique())) + "."
)
