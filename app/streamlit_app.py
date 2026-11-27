"""Application Radar (Streamlit).

Lancer : uv run streamlit run app/streamlit_app.py

Carte à deux couches (D8) :
- 🔵 Offres réelles (T39) : offres actuelles filtrées sur le domaine et le contrat visé ;
- 🟠 Candidature spontanée (T40) : entreprises du rayon sans offre correspondante, classées par
  score (radar/spontaneous.py) ; il faut une adresse (géocodée par la Géoplateforme).
"""

from __future__ import annotations

import html
import math

import folium
import pandas as pd
import streamlit as st
from compte import account_sidebar, search_history  # app/compte.py (T48, T49)
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from radar.config import FILES
from radar.domains import classify, load_domains
from radar.filters import SECTIONS, TAILLES, filter_companies
from radar.geo import region_of
from radar.geocode import Place, geocode
from radar.process.quick_filter import load_raw_offers, prepare_offers
from radar.spontaneous import haversine_km, load_nearby, rank_spontaneous

BLUE = "#1f6feb"
ORANGE = "#e8590c"
FRANCE_CENTER = (46.6, 2.4)
MAX_OFFERS_IN_POPUP = 25
MAX_SPONTANEOUS_ON_MAP = 300  # au-delà, la carte devient illisible (la liste garde tout)
RAYONS = [5, 10, 20, 30, 50, 75, 100]

st.set_page_config(page_title="Radar", page_icon="📡", layout="wide")


@st.cache_data(show_spinner="Chargement des offres…")
def get_offers() -> pd.DataFrame:
    df = prepare_offers(load_raw_offers())
    if df.empty:
        return df
    # Adzuna donne la région de sa requête ; les autres sources (LBA) : déduite du code postal.
    from_cp = df["code_postal"].astype("string").str[:2].map(region_of)
    region = df["region_requete"] if "region_requete" in df else pd.Series(pd.NA, index=df.index)
    # Domaine de chaque offre (T41) : même classifieur que T13 (code ROME + titre), calculé une
    # fois par couple (titre, ROME) distinct.
    rome = df["code_rome"] if "code_rome" in df else pd.Series(None, index=df.index)
    pairs = pd.DataFrame({"titre": df["titre"], "code_rome": rome}).astype(object)
    pairs = pairs.where(pairs.notna(), None)
    keys = list(zip(pairs["titre"], pairs["code_rome"], strict=True))
    domains = {k: classify(*k) for k in set(keys)}
    return df.assign(region_requete=region.fillna(from_cp), domaine=[domains[k] for k in keys])


@st.cache_data(show_spinner="Recherche de l'adresse…", ttl=3600)
def get_place(address: str) -> Place | None:
    return geocode(address)


@st.cache_data(show_spinner="Recherche des entreprises proches…")
def get_nearby(lat: float, lon: float, radius_km: float, domaine: str) -> pd.DataFrame:
    if not (FILES["entreprises"].exists() and FILES["scores"].exists()):
        return pd.DataFrame()
    return load_nearby(lat, lon, radius_km, domaine)


def filter_offers(
    df: pd.DataFrame,
    regions: list[str],
    contrat: str,
    domaine: str | None,
    max_age: int,
    query: str,
) -> pd.DataFrame:
    """Offres affichées en bleu ; `domaine=None` : tous domaines confondus."""
    out = df
    if domaine:
        out = out[out["domaine"] == domaine]
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


def _company_popup(r: pd.Series) -> str:
    """Fiche courte d'une entreprise de la couche orange (texte échappé)."""
    name = r.get("nom_etablissement") if pd.notna(r.get("nom_etablissement")) else None
    legal = str(r.get("nom") or "Entreprise")
    title = html.escape(f"{name} ({legal})" if name and name != legal else legal)
    lines = [
        html.escape(str(r.get("commune") or "")) + f" · {r['distance_km']:.1f} km",
        html.escape(str(r.get("naf_libelle") or "Secteur inconnu")),
    ]
    if pd.notna(r.get("tranche_effectif")):
        lines.append(f"Effectif : {html.escape(str(r['tranche_effectif']))}")
    n_dom = int(r.get("n_offres_domaine_siren", r.get("n_offres_domaine", 0)) or 0)
    signal = (
        f"{n_dom} offre{'s' if n_dom > 1 else ''} du domaine, mais aucune pour ton contrat"
        if n_dom
        else "aucune offre publiée : besoin estimé d'après le secteur et la taille"
    )
    url = html.escape(r["url_annuaire"], quote=True)
    return (
        f"<div style='font-family:sans-serif;font-size:13px'>"
        f"<b>{title}</b><br><span style='color:#555'>{'<br>'.join(lines)}</span><br>"
        f"<b style='color:{ORANGE}'>Score {r['score']:.2f}</b> · {signal}<br>"
        f'<a href="{url}" target="_blank" rel="noopener">Annuaire des entreprises</a></div>'
    )


def build_map(
    offers: pd.DataFrame,
    spontaneous: pd.DataFrame | None = None,
    place: Place | None = None,
    radius_km: float | None = None,
) -> folium.Map:
    if place is not None:
        center = (place.lat, place.lon)
        zoom = 12 if (radius_km or 20) <= 10 else 10 if radius_km <= 30 else 9
    elif offers.empty:
        center, zoom = FRANCE_CENTER, 6
    else:
        center, zoom = (offers["lat"].median(), offers["lon"].median()), 7
    m = folium.Map(location=center, zoom_start=zoom, tiles="OpenStreetMap", control_scale=True)

    if place is not None:
        folium.Marker(
            (place.lat, place.lon),
            tooltip=f"📍 {place.label}",
            icon=folium.Icon(color="black", icon="home"),
        ).add_to(m)
        if radius_km:
            folium.Circle(
                (place.lat, place.lon),
                radius=radius_km * 1000,
                color="#555",
                weight=1,
                fill=False,
                dash_array="6",
            ).add_to(m)

    if spontaneous is not None and not spontaneous.empty:
        orange = folium.FeatureGroup(name="🟠 Candidature spontanée", show=True)
        for _, r in spontaneous.head(MAX_SPONTANEOUS_ON_MAP).iloc[::-1].iterrows():
            folium.CircleMarker(
                location=(r["lat"], r["lon"]),
                radius=4 + 8 * float(r["score"]),
                color=ORANGE,
                weight=1,
                fill=True,
                fill_color=ORANGE,
                fill_opacity=0.35 + 0.5 * float(r["score"]),
                tooltip=f"{r.get('nom') or ''} — score {r['score']:.2f}",
                popup=folium.Popup(_company_popup(r), max_width=340),
            ).add_to(orange)
        orange.add_to(m)

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

DOMAINS = load_domains()  # radar/domains.yaml : clé → Domain (libellé, ROME, mots-clés)
DOMAINES = list(DOMAINS)
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
    "adresse": None,
    "rayon": RAYONS,
    "tailles": list(TAILLES),
    "secteurs": list(SECTIONS),
}
# Libellés affichés dans « Mes recherches » (T49).
PROFILE_LABELS = {
    "domaine": "Domaine",
    "contrat": "Contrat",
    "regions": "Régions",
    "query": "Mot-clé",
    "max_age": "Moins de (jours)",
    "only_data": "Seulement le domaine",
    "adresse": "Adresse",
    "rayon": "Rayon (km)",
    "tailles": "Taille",
    "secteurs": "Secteur",
}
# Valeurs par défaut posées dans session_state (et non via value=) pour qu'un profil chargé
# puisse les remplacer sans avertissement de Streamlit.
st.session_state.setdefault("max_age", 60)
st.session_state.setdefault("only_data", True)
st.session_state.setdefault("rayon", 20)

with st.sidebar:
    account_sidebar(PROFILE_KEYS)
    st.divider()
    st.header("Ta recherche")
    adresse = st.text_input(
        "Ton adresse (ou ta ville)",
        placeholder="ex. 51 rue Blaise Pascal, Bruz",
        key="adresse",
        help="Géocodée par la Géoplateforme (IGN). Nécessaire pour la couche orange.",
    )
    rayon = st.select_slider("Rayon (km)", RAYONS, key="rayon")
    domaine = st.selectbox(
        "Domaine",
        DOMAINES,
        key="domaine",
        format_func=lambda k: DOMAINS[k].label,
        help="Métiers visés (radar/domains.yaml) : filtre les offres 🔵 et choisit le score 🟠.",
    )
    contrat = st.radio("Contrat visé", CONTRATS, horizontal=True, key="contrat")
    regions = st.multiselect(
        "Régions", all_regions, placeholder="Toutes les régions collectées", key="regions"
    )
    query = st.text_input(
        "Mot-clé (titre ou entreprise)", placeholder="ex. python, Arkéa…", key="query"
    )
    max_age = st.slider("Publiées il y a moins de (jours)", 7, 60, step=7, key="max_age")
    only_data = st.toggle(
        "Seulement les offres du domaine",
        key="only_data",
        help="Classement des offres par code ROME et mots-clés du titre (T13). "
        "Désactivé : toutes les offres collectées, quel que soit le métier.",
    )
    st.subheader("Entreprises 🟠")
    tailles = st.multiselect(
        "Taille (salariés)",
        list(TAILLES),
        key="tailles",
        placeholder="Toutes les tailles",
        help="Tranche d'effectif SIRENE de l'établissement (10 salariés et plus).",
    )
    secteurs = st.multiselect(
        "Secteur d'activité",
        list(SECTIONS),
        key="secteurs",
        format_func=lambda c: f"{c} · {SECTIONS[c]}",
        placeholder="Tous les secteurs",
        help="Section NAF de l'établissement (Insee).",
    )
    st.divider()
    st.markdown(
        f"<span style='color:{BLUE}'>●</span> **Offres réelles** : annonces en ligne (Adzuna)<br>"
        f"<span style='color:{ORANGE}'>●</span> **Candidature spontanée** : entreprises du rayon "
        "**sans offre correspondante** mais avec un besoin estimé dans le domaine "
        "(plus le point est gros et foncé, plus le score est élevé)",
        unsafe_allow_html=True,
    )

view = filter_offers(
    offers, regions, contrat, domaine if only_data else None, max_age, query.strip()
)

# Couche orange (T40) : adresse → géocodage → entreprises du rayon sans offre correspondante.
place = get_place(adresse.strip()) if adresse.strip() else None
spontaneous = pd.DataFrame()
if adresse.strip() and place is None:
    st.warning(f"Adresse introuvable : « {adresse} ». Essaie une ville ou un code postal.")
if place is not None:
    view = view[haversine_km(place.lat, place.lon, view["lat"], view["lon"]) <= rayon]
    nearby = get_nearby(place.lat, place.lon, float(rayon), domaine)
    nearby = filter_companies(nearby, tailles, secteurs)  # T41
    if nearby.empty and not FILES["scores"].exists():
        st.info(
            "Pas encore de `scores.parquet` : lance `uv run python scripts/build_all.py` "
            "(ou `scripts/make_fake_data.py` pour des données factices)."
        )
    spontaneous = rank_spontaneous(nearby, place.lat, place.lon, rayon, contrat)
# Connecté : enregistre la recherche et affiche « Mes recherches » ; anonyme : ne fait rien (T49).
# Avec une adresse : SIRET des premières entreprises de la couche orange (consigne CLAUDE.md).
search_history(
    PROFILE_KEYS,
    n_results=len(view) + len(spontaneous),
    top=(
        spontaneous["siret"].head(5).astype(str).tolist()
        if not spontaneous.empty
        else view["entreprise_nom"].value_counts().head(5).index.tolist()
    ),
    labels=PROFILE_LABELS,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Offres", f"{len(view):,}".replace(",", " "))
c2.metric("Entreprises qui recrutent", f"{view['entreprise_nom'].nunique():,}".replace(",", " "))
c3.metric("Stages / alternances", int(view["contrat"].isin(["stage", "alternance"]).sum()))
c4.metric(
    "Candidatures spontanées",
    f"{len(spontaneous):,}".replace(",", " ") if place is not None else "—",
    help="Entreprises du rayon sans offre correspondante (il faut saisir une adresse).",
)
if place is not None:
    st.caption(f"📍 {place.label} · rayon {rayon} km")
else:
    st.info("Saisis ton adresse dans la barre latérale pour voir les entreprises 🟠 à démarcher.")

if view.empty and spontaneous.empty:
    st.warning("Aucune offre ni entreprise ne correspond à ces filtres.")
else:
    st_folium(
        build_map(view, spontaneous, place, rayon if place is not None else None),
        height=620,
        use_container_width=True,
        returned_objects=[],
    )

tab_offers, tab_spont = st.tabs(
    [f"🔵 Offres ({len(view)})", f"🟠 Candidatures spontanées ({len(spontaneous)})"]
)
with tab_offers:
    if view.empty:
        st.write("Aucune offre ne correspond à ces filtres.")
    else:
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
with tab_spont:
    if place is None:
        st.write("Saisis ton adresse pour voir les entreprises à démarcher.")
    elif spontaneous.empty:
        st.write(
            "Aucune entreprise trouvée : élargis le rayon ou retire des filtres (taille, secteur)."
        )
    else:
        n_col = (
            "n_offres_domaine_siren"
            if "n_offres_domaine_siren" in spontaneous
            else ("n_offres_domaine")
        )
        cols = {
            "nom": "Entreprise",
            "nom_etablissement": "Établissement",
            "commune": "Lieu",
            "distance_km": "Distance (km)",
            "naf_libelle": "Secteur",
            "tranche_effectif": "Effectif",
            "score": "Score",
            "c_intensite": "Intensité domaine",
            "c_embauche": "Besoin attendu",
            n_col: "Offres du domaine (autre contrat)",
            "url_annuaire": "Fiche",
        }
        table = spontaneous[[c for c in cols if c in spontaneous]].rename(columns=cols)
        st.dataframe(
            table,
            hide_index=True,
            width="stretch",
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Score", min_value=0.0, max_value=1.0, format="%.2f"
                ),
                "Distance (km)": st.column_config.NumberColumn(format="%.1f"),
                "Intensité domaine": st.column_config.NumberColumn(format="%.2f"),
                "Besoin attendu": st.column_config.NumberColumn(format="%.2f"),
                "Fiche": st.column_config.LinkColumn("Fiche", display_text="Annuaire"),
            },
        )
        st.caption(
            "Score v0 (D13) : moyenne géométrique de l'intensité de l'entreprise dans le domaine "
            "et de son besoin attendu (rangs centiles, 0 à 1). Les poids seront réglables (T42)."
        )

SOURCE_LABELS = {"adzuna": "Adzuna", "lba": "La bonne alternance"}
sources = ", ".join(SOURCE_LABELS.get(s, s) for s in sorted(offers["source"].dropna().unique()))
st.caption(
    f"Offres : {sources}, collecte du {str(offers['date_collecte'].max())[:10]}. "
    "Régions : " + ", ".join(all_regions) + ". "
    "Entreprises : SIRENE (Insee) ; score v0 (D13)."
)
