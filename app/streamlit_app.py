"""Application Radar (Streamlit).

Lancer : uv run streamlit run app/streamlit_app.py

Carte à deux couches (D8) :
- 🔵 Offres réelles (T39) : offres actuelles filtrées sur le domaine et le contrat visé ;
- 🟠 Candidature spontanée (T40) : entreprises du rayon sans offre correspondante, classées par
  score (radar/spontaneous.py) ; il faut choisir sa ville dans le suggesteur (T55).
"""

from __future__ import annotations

import html
import math

import folium
import pandas as pd
import streamlit as st
from compte import account_sidebar, search_history  # app/compte.py (T48, T49)
from fiche_ui import render_fiche  # app/fiche_ui.py (T43)
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from radar.communes import load_communes, place_of
from radar.config import FILES
from radar.domains import classify, load_domains
from radar.filters import SECTIONS, TAILLES, filter_companies
from radar.geo import region_of
from radar.geocode import Place
from radar.process.quick_filter import load_raw_offers, prepare_offers
from radar.recruteurs import mark_lba_recruiters
from radar.response.predict import add_p_reponse, contracts_for, load_coefficients
from radar.spontaneous import (
    COMPONENTS,
    DEFAULT_WEIGHTS,
    LBB_SOURCE,
    haversine_km,
    load_nearby,
    rank_spontaneous,
    signaled_by_lbb,
)

BLUE = "#1f6feb"
ORANGE = "#e8590c"
FRANCE_CENTER = (46.6, 2.4)
MAX_OFFERS_IN_POPUP = 25
MAX_SPONTANEOUS_ON_MAP = 300  # au-delà, la carte devient illisible (la liste garde tout)
RAYONS = [5, 10, 20, 30, 50, 75, 100]
# Curseurs de poids du score orange (T42) : composante → clé du widget (enregistrée au profil).
WEIGHT_KEYS = {c: "poids_" + c.removeprefix("c_") for c in COMPONENTS}
WEIGHT_MAX = 5
# Classement de la couche orange (T37) : score explicable ou P(réponse) du démonstrateur (D18).
TRI_SCORE, TRI_P = "Score", "P(réponse) simulée"
TRIS = [TRI_SCORE, TRI_P]
SIMULATED_BANNER = (
    "🧪 **Démonstrateur — réponses simulées.** P(réponse) vient d'un modèle entraîné sur des "
    "réponses **simulées** (aucune donnée ouverte ne dit qui répond aux candidatures "
    "spontanées) : les entreprises sont réelles, les probabilités ne le sont pas. "
    "Détails : `docs/MODELE_REPONSE.md`."
)

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


@st.cache_data(show_spinner="Chargement de la liste des communes…", ttl=24 * 3600)
def get_communes() -> pd.DataFrame:
    """Communes de France « Nom (code postal) » pour le suggesteur de ville (T55)."""
    return load_communes()


@st.cache_data
def get_coefficients() -> dict[str, float] | None:
    return load_coefficients()


@st.cache_data(show_spinner="Recherche des entreprises proches…")
def get_nearby(lat: float, lon: float, radius_km: float, domaine: str) -> pd.DataFrame:
    if not (FILES["entreprises"].exists() and FILES["scores"].exists()):
        return pd.DataFrame()
    # T51 : marque les recruteurs potentiels LBA sur un métier du domaine (`recruteur_lba`).
    return mark_lba_recruiters(load_nearby(lat, lon, radius_km, domaine), domaine)


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
        f"{_explication_html(r)}"
        f"{_procedure_html(r)}"
        f"{_lbb_html(r)}"
        f"{_p_reponse_html(r)}"
        f"{_score_breakdown_html(r)}"
        f'<a href="{url}" target="_blank" rel="noopener">Annuaire des entreprises</a></div>'
    )


def _explication_html(r: pd.Series) -> str:
    """T32 : « Recommandée car … » (radar/explain.py), en italique, texte échappé."""
    txt = r.get("explication")
    if not isinstance(txt, str) or not txt:
        return ""
    return f"<i style='color:#333'>{html.escape(txt)}</i><br>"


def _lbb_html(r: pd.Series) -> str:
    """T29 (D27) : établissement signalé par La Bonne Boîte comme susceptible d'embaucher."""
    if r.get("c_embauche_source") != LBB_SOURCE:
        return ""
    pot = r.get("lbb_potentiel")
    detail = f" (potentiel {float(pot):.1f})" if pd.notna(pot) else ""
    return (
        f"<span style='color:#1b5e20'>✔ Signalée par La Bonne Boîte (France Travail)"
        f"{detail}</span><br>"
    )


def _procedure_html(r: pd.Series) -> str:
    """Alerte BODACC (T23, D24) : situation défavorable, score réduit, lien vers l'annonce."""
    alerte = r.get("alerte")
    if not alerte or pd.isna(alerte):
        return ""
    url = r.get("procedure_url")
    link = (
        f' · <a href="{html.escape(str(url), quote=True)}" target="_blank" '
        'rel="noopener">BODACC</a>'
        if isinstance(url, str) and url
        else ""
    )
    return (
        f"<span style='color:#b00020'>{html.escape(str(alerte))}</span>{link}<br>"
        f"<span style='color:#555;font-size:11px'>Score réduit (×{float(r['coef_procedure']):.2f})"
        "</span><br>"
    )


def _p_reponse_html(r: pd.Series) -> str:
    """P(réponse) du démonstrateur (T37), toujours marquée comme simulée."""
    p = r.get("p_reponse")
    if p is None or pd.isna(p):
        return ""
    return f"P(réponse) <i>simulée</i> : <b>{100 * float(p):.0f} %</b><br>"


def _score_breakdown_html(r: pd.Series) -> str:
    """Décomposition du score (T42) : apport de chaque composante active, en barres."""
    rows = []
    for c, (label, _) in COMPONENTS.items():
        apport = r.get(f"apport_{c}")
        if apport is None or pd.isna(apport) or not st.session_state.get(WEIGHT_KEYS[c]):
            continue
        width = int(round(100 * float(apport)))
        rows.append(
            f"<tr><td style='padding-right:6px'>{html.escape(label)}</td>"
            f"<td style='width:90px'><div style='background:{ORANGE};height:8px;"
            f"width:{width}px;max-width:90px'></div></td>"
            f"<td style='text-align:right'>+{float(apport):.2f}</td></tr>"
        )
    if not rows:
        return ""
    return "<table style='font-size:12px;color:#333;margin:4px 0'>" + "".join(rows) + "</table>"


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
communes = get_communes()
COMMUNE_LABELS = communes["label"].tolist()

# Réglages enregistrés dans le profil quand on est connecté (T48) : clé du widget → options
# permises (None = libre). Ajouter ici la clé de tout nouveau réglage (T40, T41, T42…).
PROFILE_KEYS = {
    "domaine": DOMAINES,
    "contrat": CONTRATS,
    "regions": all_regions,
    "query": None,
    "max_age": list(range(7, 61, 7)) + [60],
    "only_data": [True, False],
    "ville": COMMUNE_LABELS,
    "rayon": RAYONS,
    "tailles": list(TAILLES),
    "secteurs": list(SECTIONS),
    **{key: list(range(WEIGHT_MAX + 1)) for key in WEIGHT_KEYS.values()},
    "tri": TRIS,
    "show_liquidation": [True, False],
}
# Libellés affichés dans « Mes recherches » (T49).
PROFILE_LABELS = {
    "domaine": "Domaine",
    "contrat": "Contrat",
    "regions": "Régions",
    "query": "Mot-clé",
    "max_age": "Moins de (jours)",
    "only_data": "Seulement le domaine",
    "ville": "Ville",
    "rayon": "Rayon (km)",
    "tailles": "Taille",
    "secteurs": "Secteur",
    **{key: f"Poids {COMPONENTS[c][0].lower()}" for c, key in WEIGHT_KEYS.items()},
    "tri": "Classement",
    "show_liquidation": "Avec liquidations",
}
# Valeurs par défaut posées dans session_state (et non via value=) pour qu'un profil chargé
# puisse les remplacer sans avertissement de Streamlit.
st.session_state.setdefault("ville", None)
st.session_state.setdefault("max_age", 60)
st.session_state.setdefault("only_data", True)
st.session_state.setdefault("rayon", 20)
st.session_state.setdefault("tri", TRI_SCORE)
st.session_state.setdefault("show_liquidation", False)
for _c, _key in WEIGHT_KEYS.items():
    st.session_state.setdefault(_key, DEFAULT_WEIGHTS[_c])


def _reset_weights() -> None:
    for c, key in WEIGHT_KEYS.items():
        st.session_state[key] = DEFAULT_WEIGHTS[c]


with st.sidebar:
    account_sidebar(PROFILE_KEYS)
    st.divider()
    st.header("Ta recherche")
    # Suggesteur (T55) : on tape le début du nom, on valide « Ville (code postal) » dans la liste.
    ville = st.selectbox(
        "Ta ville",
        COMMUNE_LABELS,
        key="ville",
        placeholder="Tape le nom de ta ville…",
        help="Tape quelques lettres puis choisis ta commune et son code postal dans la liste. "
        "Nécessaire pour la couche orange (distance depuis le centre de la commune).",
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
    show_liquidation = st.checkbox(
        "Afficher aussi les entreprises en liquidation",
        key="show_liquidation",
        help="BODACC (T23) : en liquidation judiciaire, l'activité est en principe arrêtée. "
        "Masquées par défaut ; les autres procédures (sauvegarde, redressement, plan) restent "
        "visibles avec une alerte et un score réduit.",
    )
    tri = st.radio(
        "Classer les entreprises 🟠 par",
        TRIS,
        key="tri",
        horizontal=True,
        help="Score : moyenne pondérée explicable (curseurs ci-dessous). P(réponse) : "
        "démonstrateur entraîné sur des réponses simulées (stage et alternance seulement).",
    )
    with st.expander("⚖️ Poids du score 🟠", expanded=True):
        st.caption("0 = ignoré. Le score est la moyenne pondérée des composantes (0 à 1).")
        weights = {
            c: st.slider(label, 0, WEIGHT_MAX, key=WEIGHT_KEYS[c], help=help_)
            for c, (label, help_) in COMPONENTS.items()
        }
        st.button("Poids par défaut", on_click=_reset_weights, width="stretch")
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

# Couche orange (T40) : ville choisie (T55) → entreprises du rayon sans offre correspondante.
place = place_of(ville, communes)
spontaneous = pd.DataFrame()
if place is not None:
    view = view[haversine_km(place.lat, place.lon, view["lat"], view["lon"]) <= rayon]
    nearby = get_nearby(place.lat, place.lon, float(rayon), domaine)
    nearby = filter_companies(nearby, tailles, secteurs)  # T41
    if nearby.empty and not FILES["scores"].exists():
        st.info(
            "Pas encore de `scores.parquet` : lance `uv run python scripts/build_all.py` "
            "(ou `scripts/make_fake_data.py` pour des données factices)."
        )
    spontaneous = rank_spontaneous(
        nearby, place.lat, place.lon, rayon, contrat, weights, show_liquidation
    )
    # P(réponse) du démonstrateur (T37, D18) : à distance nulle + effet de la distance.
    spontaneous = add_p_reponse(spontaneous, domaine, contrat, get_coefficients())
    if tri == TRI_P and spontaneous["p_reponse"].notna().any():
        spontaneous = spontaneous.sort_values(
            ["p_reponse", "score"], ascending=False, na_position="last"
        ).reset_index(drop=True)
# Connecté : enregistre la recherche et affiche « Mes recherches » ; anonyme : ne fait rien (T49).
# Avec une ville : noms des premières entreprises de la couche orange (consigne CLAUDE.md).
search_history(
    PROFILE_KEYS,
    n_results=len(view) + len(spontaneous),
    top=(
        spontaneous["nom"].head(5).astype(str).tolist()  # noms lisibles dans « Mes recherches »
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
    help="Entreprises du rayon sans offre correspondante (il faut choisir ta ville).",
)
if place is not None:
    st.caption(f"📍 {place.label} · rayon {rayon} km")
    has_p = "p_reponse" in spontaneous and spontaneous["p_reponse"].notna().any()
    if tri == TRI_P or has_p:
        st.warning(SIMULATED_BANNER)
    if tri == TRI_P and not has_p and not spontaneous.empty:
        if get_coefficients() is None or not FILES["p_reponse"].exists():
            why = "le modèle n'est pas construit (`uv run python scripts/build_response.py`)"
        elif not contracts_for(contrat):
            why = "le modèle ne couvre que le stage et l'alternance"
        else:
            why = f"le modèle ne couvre pas encore le domaine « {DOMAINS[domaine].label} »"
        st.info(f"P(réponse) indisponible : {why}. Classement par score.")
else:
    st.info("Choisis ta ville dans la barre latérale pour voir les entreprises 🟠 à démarcher.")

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
        st.write("Choisis ta ville pour voir les entreprises à démarcher.")
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
            "alerte": "Situation",  # BODACC (T23) : vide si rien à signaler
            "signal_lbb": "La Bonne Boîte",  # T29 : ✔ si signalée par La Bonne Boîte (D27)
            "nom_etablissement": "Établissement",
            "commune": "Lieu",
            "distance_km": "Distance (km)",
            "naf_libelle": "Secteur",
            "tranche_effectif": "Effectif",
            "score": "Score",
            "p_reponse": "P(réponse) simulée",
            # Apport de chaque composante active au score (T42) : la somme des apports = score.
            **{
                f"apport_{c}": f"+ {label}"
                for c, (label, _) in COMPONENTS.items()
                if weights.get(c)
            },
            n_col: "Offres du domaine (autre contrat)",
            "url_annuaire": "Fiche",
        }
        spontaneous = spontaneous.assign(
            signal_lbb=signaled_by_lbb(spontaneous).map({True: "✔", False: ""})
        )
        shown = [
            c
            for c in cols
            if c in spontaneous
            and spontaneous[c].notna().any()
            and (c not in ("alerte", "signal_lbb") or spontaneous[c].astype(bool).any())
        ]
        table = spontaneous[shown].rename(columns=cols)
        st.dataframe(
            table,
            hide_index=True,
            width="stretch",
            column_config={
                "P(réponse) simulée": st.column_config.NumberColumn(
                    format="percent",
                    help="Démonstrateur entraîné sur des réponses SIMULÉES (D18), "
                    "ajustée de la distance.",
                ),
                "Score": st.column_config.ProgressColumn(
                    "Score", min_value=0.0, max_value=1.0, format="%.2f"
                ),
                "Distance (km)": st.column_config.NumberColumn(format="%.1f"),
                **{
                    f"+ {label}": st.column_config.NumberColumn(format="%.2f", help=help_)
                    for label, help_ in COMPONENTS.values()
                },
                "Fiche": st.column_config.LinkColumn("Fiche", display_text="Annuaire"),
            },
        )
        st.caption(
            "Score = moyenne pondérée des composantes, avec tes poids (barre latérale). "
            "Les colonnes « + … » donnent l'apport de chaque composante (leur somme = le score). "
            "Intensité : rang centile du modèle bayésien empirique (D13). "
            "Potentiel d'embauche : établissements signalés par La Bonne Boîte (✔) en tête, "
            "estimation pour les autres (D27)."
        )
    # Fiche détaillée d'une entreprise de la liste (T43, @celia) — panneau sous la liste.
    render_fiche(spontaneous)

SOURCE_LABELS = {"adzuna": "Adzuna", "lba": "La bonne alternance"}
sources = ", ".join(SOURCE_LABELS.get(s, s) for s in sorted(offers["source"].dropna().unique()))
st.caption(
    f"Offres : {sources}, collecte du {str(offers['date_collecte'].max())[:10]}. "
    "Régions : " + ", ".join(all_regions) + ". "
    "Entreprises : SIRENE (Insee) ; score D13 pondéré par tes poids (T42)."
)
