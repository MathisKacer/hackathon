"""Ce que les pages de l'app partagent : constantes, chargement des données, réglages du profil.

Les réglages de recherche (widgets de la page Explorer) sont enregistrés dans le profil quand
on est connecté (T48) : voir PROFILE_KEYS. Règle pour ajouter un réglage : CLAUDE.md.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from radar.communes import load_communes, place_of
from radar.config import FILES
from radar.domains import classify, load_domains
from radar.filters import SECTIONS, TAILLES
from radar.geo import region_of
from radar.geocode import Place
from radar.process.quick_filter import load_raw_offers, prepare_offers
from radar.recruteurs import mark_lba_recruiters
from radar.response.predict import load_coefficients
from radar.spontaneous import COMPONENTS, DEFAULT_WEIGHTS, load_nearby

PAGES_DIR = (
    Path(__file__).resolve().parent / "vues"
)  # chemins absolus : marche quel que soit le lanceur
BLUE = "#1f6feb"  # offres publiées (carte)
ORANGE = "#e8590c"  # candidatures spontanées (carte)
RAYONS = [5, 10, 20, 30, 50, 75, 100]
CONTRATS = ["Tous", "Stage", "Alternance", "Emploi"]
# Curseurs de poids du score orange (T42) : composante → clé du widget (enregistrée au profil).
WEIGHT_KEYS = {c: "poids_" + c.removeprefix("c_") for c in COMPONENTS}
WEIGHT_MAX = 5
# Classement des candidatures spontanées (T37) : score ou chance de réponse du démonstrateur.
TRI_SCORE, TRI_P = "Score", "Chance de réponse (démo)"
TRIS = [TRI_SCORE, TRI_P]
SIMULATED_BANNER = (
    "**Démonstration.** La chance de réponse vient d'un modèle entraîné sur des réponses "
    "simulées : aucune donnée publique ne dit quelles entreprises répondent aux candidatures "
    "spontanées. Les entreprises sont réelles, ces pourcentages ne le sont pas."
)
DOMAINS = load_domains()  # radar/domains.yaml : clé → Domain (libellé, ROME, mots-clés)
DOMAINES = list(DOMAINS)

# Clés de tous les widgets de recherche : conservées quand on change de page (voir persist).
WIDGET_KEYS = [
    "ville",
    "rayon",
    "domaine",
    "contrat",
    "regions",
    "query",
    "max_age",
    "only_data",
    "tailles",
    "secteurs",
    "show_liquidation",
    "tri",
    *WEIGHT_KEYS.values(),
]


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


def get_place(ville: str | None) -> Place | None:
    """Position de la commune choisie dans le suggesteur (T55) ; None si rien n'est choisi."""
    return place_of(ville, get_communes())


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


def profile_keys(all_regions: list[str]) -> dict[str, list | None]:
    """Réglages enregistrés dans le profil : clé du widget → options permises (None = libre)."""
    commune_labels = get_communes()["label"].tolist()
    return {
        "domaine": DOMAINES,
        "contrat": CONTRATS,
        "regions": all_regions,
        "query": None,
        "max_age": list(range(7, 61, 7)) + [60],
        "only_data": [True, False],
        "ville": commune_labels,  # suggesteur de ville (T55)
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


def all_regions_of(offers: pd.DataFrame) -> list[str]:
    return sorted(offers["region_requete"].dropna().unique()) if not offers.empty else []


def init_defaults() -> None:
    """Valeurs par défaut dans session_state (et non via value=) : un profil peut les remplacer."""
    st.session_state.setdefault("ville", None)
    st.session_state.setdefault("rayon", 20)
    st.session_state.setdefault("domaine", DOMAINES[0])
    st.session_state.setdefault("contrat", "Tous")
    st.session_state.setdefault("max_age", 60)
    st.session_state.setdefault("only_data", True)
    st.session_state.setdefault("tri", TRI_SCORE)
    st.session_state.setdefault("show_liquidation", False)
    for c, key in WEIGHT_KEYS.items():
        st.session_state.setdefault(key, DEFAULT_WEIGHTS[c])


def persist_widget_state() -> None:
    """Garde les réglages quand on change de page.

    Streamlit oublie la valeur d'un widget qui n'est pas affiché pendant une exécution : sans
    cette ligne, aller sur « Entreprises » puis revenir effacerait la recherche.
    """
    for key in WIDGET_KEYS:
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]


def reset_weights() -> None:
    for c, key in WEIGHT_KEYS.items():
        st.session_state[key] = DEFAULT_WEIGHTS[c]


def current_weights() -> dict[str, int]:
    return {c: st.session_state.get(key, DEFAULT_WEIGHTS[c]) for c, key in WEIGHT_KEYS.items()}


__all__ = [
    "FILES",
    "Place",
]
