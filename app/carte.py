"""Carte folium de l'app (D8) : offres publiées en bleu, candidatures spontanées en orange.

Déplacé tel quel depuis app/streamlit_app.py (découpage en pages). Le popup d'une entreprise
(`_company_popup`) est la zone de T32 (@mathis).
"""

from __future__ import annotations

import html
import math

import folium
import pandas as pd
import streamlit as st
from commun import BLUE, ORANGE, WEIGHT_KEYS
from folium.plugins import MarkerCluster

from radar.geocode import Place
from radar.spontaneous import COMPONENTS, LBB_SOURCE

FRANCE_CENTER = (46.6, 2.4)
MAX_OFFERS_IN_POPUP = 25
MAX_SPONTANEOUS_ON_MAP = 300  # au-delà, la carte devient illisible (la liste garde tout)


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
    """Chance de réponse (T37, T64) : modèle entraîné sur des réponses simulées (D23)."""
    p = r.get("p_reponse")
    if p is None or pd.isna(p):
        return ""
    # T64 : libellé clair ; mention « simulée » dans les info-bulles (liste, fiche)
    return f"Chance de réponse : <b>{100 * float(p):.0f} %</b><br>"


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
