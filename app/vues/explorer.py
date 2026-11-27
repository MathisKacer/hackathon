"""Page « Explorer » : où candidater autour de soi.

Recherche en haut (où, contrat, domaine, rayon) + bouton « Filtres » ; carte ; onglets
Candidatures spontanées / Offres ; clic sur une entreprise → fiche dans une fenêtre (T43).
Logique de classement inchangée : radar/spontaneous.py (T40, T41, T42, T23), T37, T51.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from carte import build_map
from commun import (
    CONTRATS,
    DOMAINES,
    DOMAINS,
    FILES,
    PAGES_DIR,
    PROFILE_LABELS,
    RAYONS,
    SIMULATED_BANNER,
    TRI_P,
    TRIS,
    WEIGHT_KEYS,
    WEIGHT_MAX,
    all_regions_of,
    current_weights,
    filter_offers,
    get_coefficients,
    get_communes,
    get_nearby,
    get_offers,
    get_place,
    profile_keys,
    reset_weights,
)
from compte import record_search
from favoris import favorite_refs, offer_ref, sync_offers_editor, temp_banner
from fiche_ui import open_fiche
from streamlit_folium import st_folium

from radar.collect.sirene import TRANCHE_LIBELLES
from radar.filters import SECTIONS, TAILLES, filter_companies
from radar.response.predict import add_p_reponse
from radar.spontaneous import COMPONENTS, haversine_km, rank_spontaneous, signaled_by_lbb

SITUATION_COURTE = {
    "sauvegarde": "🟡 Sauvegarde",
    "plan": "🟡 Plan",
    "redressement": "🟠 Redressement",
    "liquidation": "🔴 Liquidation",
}


def _n_filters_on() -> int:
    """Nombre de filtres modifiés (affiché sur le bouton « Filtres »)."""
    ss = st.session_state
    return sum(
        [
            bool(ss.get("regions")),
            bool(str(ss.get("query", "")).strip()),
            ss.get("max_age", 60) != 60,
            not ss.get("only_data", True),
            bool(ss.get("tailles")),
            bool(ss.get("secteurs")),
            bool(ss.get("show_liquidation")),
            ss.get("tri") == TRI_P,
        ]
    )


offers = get_offers()
if offers.empty:
    st.title("Radar")
    st.info("Aucune offre n'est chargée pour le moment.")
    st.caption("Équipe : lancer la collecte ou récupérer `data/raw/offres_raw/` (voir CLAUDE.md).")
    st.stop()

all_regions = all_regions_of(offers)
PROFILE_KEYS = profile_keys(all_regions)

# ------------------------------------------------------------------ recherche
st.title("Où candidater ?")
st.caption(
    "Les offres publiées autour de toi, et les entreprises qui recrutent dans ton domaine "
    "sans avoir publié d'offre pour ton contrat : les meilleures cibles de candidature spontanée."
)

with st.container(border=True):
    c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
    # Suggesteur de ville (T55) : on tape le début du nom, on choisit « Ville (code postal) ».
    ville = c1.selectbox(
        "Où ?",
        get_communes()["label"].tolist(),
        key="ville",
        placeholder="Tape le nom de ta ville…",
    )
    contrat = c2.segmented_control("Contrat", CONTRATS, key="contrat", required=True) or "Tous"
    c3, c4, c5 = st.columns([3, 1, 1], vertical_alignment="bottom")
    domaine = c3.selectbox(
        "Domaine", DOMAINES, key="domaine", format_func=lambda k: DOMAINS[k].label
    )
    rayon = c4.selectbox("Rayon", RAYONS, key="rayon", format_func=lambda r: f"{r} km")
    n_on = _n_filters_on()
    with c5.popover(f"Filtres ({n_on})" if n_on else "Filtres", width="stretch"):
        st.markdown("**Offres**")
        regions = st.multiselect(
            "Régions", all_regions, key="regions", placeholder="Toutes les régions"
        )
        query = st.text_input("Mot-clé", key="query", placeholder="ex. python, Arkéa…")
        max_age = st.slider("Publiées il y a moins de (jours)", 7, 60, step=7, key="max_age")
        only_data = st.toggle("Seulement les offres du domaine", key="only_data")
        st.markdown("**Entreprises**")
        tailles = st.multiselect(
            "Taille", list(TAILLES), key="tailles", placeholder="Toutes les tailles"
        )
        secteurs = st.multiselect(
            "Secteur",
            list(SECTIONS),
            key="secteurs",
            format_func=lambda c: SECTIONS[c],
            placeholder="Tous les secteurs",
        )
        show_liquidation = st.checkbox(
            "Afficher aussi les entreprises en liquidation",
            key="show_liquidation",
            help="Leur activité est en principe arrêtée. Les autres entreprises en difficulté "
            "restent affichées, avec une alerte.",
        )
        st.markdown("**Classement**")
        tri = st.radio("Classer par", TRIS, key="tri", horizontal=True)
        st.caption("Importance de chaque critère dans le score (0 = ignoré) :")
        for c, (label, help_) in COMPONENTS.items():
            st.slider(label, 0, WEIGHT_MAX, key=WEIGHT_KEYS[c], help=help_)
        st.button("Revenir aux réglages par défaut", on_click=reset_weights, width="stretch")
weights = current_weights()

# ------------------------------------------------------------------ calculs
view = filter_offers(
    offers, regions, contrat, domaine if only_data else None, max_age, query.strip()
)
place = get_place(ville)
spontaneous = pd.DataFrame()
if place is not None:
    view = view[haversine_km(place.lat, place.lon, view["lat"], view["lon"]) <= rayon]
    nearby = filter_companies(
        get_nearby(place.lat, place.lon, float(rayon), domaine), tailles, secteurs
    )
    spontaneous = rank_spontaneous(
        nearby, place.lat, place.lon, rayon, contrat, weights, show_liquidation
    )
    spontaneous = add_p_reponse(spontaneous, domaine, contrat, get_coefficients())
    if tri == TRI_P and spontaneous["p_reponse"].notna().any():
        spontaneous = spontaneous.sort_values(
            ["p_reponse", "score"], ascending=False, na_position="last"
        ).reset_index(drop=True)

# Connecté : la recherche est enregistrée (« Mes recherches », page Mon espace).
record_search(
    PROFILE_KEYS,
    n_results=len(view) + len(spontaneous),
    top=(
        spontaneous["nom"].head(5).astype(str).tolist()
        if not spontaneous.empty
        else view["entreprise_nom"].value_counts().head(5).index.tolist()
    ),
)

# ------------------------------------------------------------------ résultat
contrat_txt = {
    "Tous": "",
    "Stage": " en stage",
    "Alternance": " en alternance",
    "Emploi": " en emploi",
}[contrat]
if place is None:
    st.markdown(
        "**Comment ça marche**  \n"
        "1. Choisis ta ville et le contrat que tu vises.  \n"
        "2. La carte montre en **bleu** les offres publiées et en **orange** les entreprises "
        "qui recrutent dans ton domaine sans offre pour ton contrat.  \n"
        "3. Clique sur une entreprise de la liste pour voir sa fiche et pourquoi elle est "
        "recommandée."
    )
else:
    st.markdown(
        f"Autour de **{place.label}** ({rayon} km) : **{len(spontaneous)}** entreprises "
        f"pourraient t'accueillir{contrat_txt} sans avoir publié d'offre, et "
        f"**{len(view)}** offres sont publiées."
    )
    if tri == TRI_P:
        st.info(SIMULATED_BANNER)
    if spontaneous.empty and not FILES["scores"].exists():
        st.caption("Équipe : `scores.parquet` manquant (lancer `scripts/build_all.py`).")

temp_banner(PAGES_DIR / "mon_espace.py")  # favoris temporaires (anonyme, T54)

if not (view.empty and spontaneous.empty):
    st_folium(
        build_map(view, spontaneous, place, rayon if place is not None else None),
        height=520,
        use_container_width=True,
        returned_objects=[],
    )

# ------------------------------------------------------------------ listes
tab_spont, tab_offers = st.tabs(
    [f"Candidatures spontanées ({len(spontaneous)})", f"Offres ({len(view)})"]
)
with tab_spont:
    if place is None:
        st.write("Choisis ta ville pour voir les entreprises à démarcher.")
    elif spontaneous.empty:
        st.write("Aucune entreprise trouvée : élargis le rayon ou retire des filtres.")
    else:
        # « Établissement (Entreprise) » quand les deux noms diffèrent, sinon le nom seul.
        etab = spontaneous.get("nom_etablissement", pd.Series(index=spontaneous.index))
        nom = [
            f"{e} ({n})" if isinstance(e, str) and e and e != n else n
            for e, n in zip(etab, spontaneous["nom"].astype(str), strict=True)
        ]
        fav = favorite_refs("entreprise")
        table = pd.DataFrame(
            {
                "★": spontaneous["siret"].astype(str).isin(fav).map({True: "★", False: ""}),
                "Entreprise": nom,
                "Lieu": spontaneous.get("commune"),
                "Distance": spontaneous["distance_km"],
                "Taille": spontaneous.get(
                    "tranche_effectif", pd.Series(index=spontaneous.index)
                ).map(TRANCHE_LIBELLES),
                "Situation": spontaneous.get(
                    "procedure_type", pd.Series(index=spontaneous.index)
                ).map(SITUATION_COURTE),
                # T29 (D27) : ✔ si La Bonne Boîte signale l'établissement comme recruteur
                "La Bonne Boîte": signaled_by_lbb(spontaneous).map({True: "✔", False: ""}),
                "Score": spontaneous["score"],
            }
        )
        if tri == TRI_P and "p_reponse" in spontaneous:
            table["Chance de réponse (démo)"] = spontaneous["p_reponse"]
        if not table["★"].astype(bool).any():
            table = table.drop(columns="★")
        if table["Situation"].isna().all():
            table = table.drop(columns="Situation")
        if not table["La Bonne Boîte"].astype(bool).any():
            table = table.drop(columns="La Bonne Boîte")
        version = st.session_state.get("_liste_version", 0)
        event = st.dataframe(
            table,
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="single-row",
            key=f"liste_spont_{version}",
            column_config={
                "Distance": st.column_config.NumberColumn(format="%.1f km"),
                "Score": st.column_config.ProgressColumn(
                    min_value=0.0, max_value=1.0, format="%.2f"
                ),
                "Chance de réponse (démo)": st.column_config.NumberColumn(format="percent"),
            },
        )
        st.caption("Clique sur une ligne pour ouvrir la fiche de l'entreprise.")
        rows = event.selection.rows if event is not None else []
        if rows:
            r = spontaneous.iloc[rows[0]]
            open_fiche(r["siret"], r, domaine)

with tab_offers:
    if view.empty:
        st.write("Aucune offre ne correspond à ta recherche.")
    else:
        ordered = view.sort_values("age_jours")
        fav_offers = favorite_refs("offre")
        table = ordered[
            ["titre", "entreprise_nom", "commune", "contrat", "age_jours", "url"]
        ].rename(
            columns={
                "titre": "Offre",
                "entreprise_nom": "Entreprise",
                "commune": "Lieu",
                "contrat": "Contrat",
                "age_jours": "Publiée il y a",
                "url": "Annonce",
            }
        )
        table.insert(0, "★", [offer_ref(r) in fav_offers for _, r in ordered.iterrows()])
        # La clé change avec la liste et les favoris : les cases repartent de l'état enregistré.
        editor_key = f"offres_{hash((tuple(table.index), tuple(sorted(fav_offers))))}"
        edited = st.data_editor(
            table,
            hide_index=True,
            width="stretch",
            key=editor_key,
            disabled=[c for c in table.columns if c != "★"],
            column_config={
                "★": st.column_config.CheckboxColumn(
                    "★", help="Ajouter aux favoris", width="small"
                ),
                "Publiée il y a": st.column_config.NumberColumn(format="%d j"),
                "Annonce": st.column_config.LinkColumn("Annonce", display_text="Voir l'offre"),
            },
        )
        st.caption("Coche ★ pour garder une offre dans tes favoris (Mon espace).")
        if sync_offers_editor(edited, table, ordered):
            st.rerun()

SOURCE_LABELS = {"adzuna": "Adzuna", "lba": "La bonne alternance"}
sources = ", ".join(SOURCE_LABELS.get(s, s) for s in sorted(offers["source"].dropna().unique()))
st.caption(
    f"Offres : {sources}, collectées le {str(offers['date_collecte'].max())[:10]}. "
    "Entreprises : répertoire SIRENE (Insee) et BODACC."
)

__all__ = ["PROFILE_LABELS"]
