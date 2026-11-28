"""Page de résultats (« Explorer ») : où candidater autour de soi.

T93 (essai) : deux blocs (recherche et filtres à gauche, carte à droite), puis la liste des
entreprises et le tableau de bord ; on y arrive depuis la page d'accueil (app/vues/accueil.py).

Recherche en haut (où, contrat, domaine, rayon) + bouton « Filtres » ; carte ; onglets
Candidatures spontanées / Offres ; clic sur une entreprise → fiche dans une fenêtre (T43).
Logique de classement inchangée : radar/spontaneous.py (T40, T41, T42, T23), T37, T51.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from carte import build_map
from commun import (
    BLUE,
    CHANCE_HELP,
    CONTRATS,
    DOMAINES,
    DOMAINS,
    FILES,
    MATCH_HELP,
    NIVEAUX,
    ORANGE,
    PAGES_DIR,
    PROFILE_LABELS,
    RAYONS,
    TRI_MATCH,
    TRI_P,
    TRIS,
    WEIGHT_KEYS,
    WEIGHT_MAX,
    current_weights,
    filter_offers,
    get_coefficients,
    get_communes,
    get_families,
    get_nearby,
    get_offers,
    get_place,
    get_skill_profile,
    get_top,
    profile_keys,
    reset_weights,
)
from cv_ui import cv_and_skills
from favoris import favorite_refs, offer_ref, sync_offers_editor, temp_banner
from fiche_ui import open_fiche
from recherches import save_button
from streamlit_folium import st_folium
from style import GREEN, LINK_STYLE, Tile, fmt_int, kpi_tiles
from tableau_bord import dashboard

from radar.collect.sirene import tranche_display
from radar.competences import MATCH_COLORS, NO_MATCH_MESSAGE, add_match, match_skills
from radar.familles import mark_family_offers
from radar.filters import SECTIONS, TAILLES, filter_companies
from radar.niveau import levels_label
from radar.paliers import (
    add_tiers,
    rule_text,
    score_color,
    text_color_on,
    tier_color,
)
from radar.response.predict import add_p_reponse
from radar.spontaneous import COMPONENTS, haversine_km, rank_spontaneous, signaled_by_lbb

MAX_LIST_ROWS = 500  # lignes affichées dans la liste des candidatures spontanées (T71)
SITUATION_COURTE = {
    "sauvegarde": "🟡 Sauvegarde",
    "plan": "🟡 Plan",
    "redressement": "🟠 Redressement",
    "liquidation": "🔴 Liquidation",
}


def _pl(n: int, word: str) -> str:
    """Accord au pluriel : _pl(2, "offre") → « offres »."""
    return word + ("s" if n > 1 else "")


offers = get_offers()
if offers.empty:
    st.title("Radar")
    st.info("Aucune offre n'est chargée pour le moment.")
    st.caption("Équipe : lancer la collecte ou récupérer `data/raw/offres_raw/` (voir CLAUDE.md).")
    st.stop()

PROFILE_KEYS = profile_keys()

# ------------------------------------------------------------------ recherche
# T93 (essai) : page de résultats en deux blocs — à gauche la recherche et tous les filtres,
# à droite la carte ; en dessous, la liste des entreprises puis le tableau de bord.
left, right = st.columns([1, 2.1], gap="large")
with left, st.container(border=True, key="carte_recherche"):
    st.markdown("<div class='radar-block-title'>Ta recherche</div>", unsafe_allow_html=True)
    # Suggesteur de ville (T55) : on tape le début du nom (ou un code postal) et on choisit
    # « Ville (codes postaux) ». index=None : la croix permet d'effacer pour changer de ville.
    ville = st.selectbox(
        "Où ?",
        get_communes()["label"].tolist(),
        index=None,
        key="ville",
        placeholder="Toute la France (ou tape ta ville)",
    )
    contrat = st.segmented_control("Contrat", CONTRATS, key="contrat", required=True) or "Tous"
    c3, c4 = st.columns([2, 1], vertical_alignment="bottom")
    domaine = c3.selectbox(
        "Domaine", DOMAINES, key="domaine", format_func=lambda k: DOMAINS[k].label
    )
    rayon = c4.selectbox("Rayon", RAYONS, key="rayon", format_func=lambda r: f"{r} km")
    with st.expander("Offres", icon=":material/work:"):
        query = st.text_input("Mot-clé", key="query", placeholder="ex. python, Arkéa…")
        max_age = st.slider("Publiées il y a moins de (jours)", 7, 60, step=7, key="max_age")
        only_data = st.toggle("Seulement les offres du domaine", key="only_data")
        # T67 (D33) : niveau d'études attendu, indiqué par La bonne alternance ou lu dans l'offre.
        niveaux = st.multiselect(
            "Niveau d'études",
            NIVEAUX,
            key="niveaux",
            placeholder="Tous les niveaux",
            help="Niveau demandé par l'offre : donné par La bonne alternance, sinon lu dans "
            "le titre et le début de l'annonce. La plupart des offres ne le précisent pas.",
        )
        niveau_inconnu = st.checkbox(
            "Garder les offres sans niveau précisé",
            key="niveau_inconnu",
            disabled=not niveaux,
        )
    with st.expander("Entreprises", icon=":material/apartment:"):
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
        une_par_entreprise = st.checkbox(
            "Une ligne par entreprise",
            key="une_par_entreprise",
            help="Garde seulement le site le mieux classé de chaque entreprise "
            "(les autres sites restent visibles dans sa fiche).",
        )
    with st.expander("Ton CV", icon=":material/description:"):
        competences = cv_and_skills("cv_fichier")  # T45, T83 : CV + compétences (saisie libre)
    with st.expander("Classement", icon=":material/tune:"):
        tri = st.radio("Classer par", TRIS, key="tri", horizontal=True)
        st.caption("Importance de chaque critère dans le score (0 = ignoré) :")
        for c, (label, help_) in COMPONENTS.items():
            st.slider(label, 0, WEIGHT_MAX, key=WEIGHT_KEYS[c], help=help_)
        st.button("Revenir aux réglages par défaut", on_click=reset_weights, width="stretch")
    save_button(PROFILE_KEYS)  # T84 : garder les réglages de cette recherche
weights = current_weights()

# ------------------------------------------------------------------ calculs
view = filter_offers(
    offers,
    contrat,
    domaine if only_data else None,
    max_age,
    query.strip(),
    niveaux,
    niveau_inconnu,
)
place = get_place(ville)
spontaneous = pd.DataFrame()
# T93 (essai) : sans ville, les meilleures candidatures spontanées de France entière (sans
# distance ni proximité) ; avec une ville, celles du rayon comme avant.
if place is not None:
    view = view[haversine_km(place.lat, place.lon, view["lat"], view["lon"]) <= rayon]
    nearby = filter_companies(
        get_nearby(place.lat, place.lon, float(rayon), domaine), tailles, secteurs
    )
    spontaneous = rank_spontaneous(
        nearby, place.lat, place.lon, rayon, contrat, weights, show_liquidation
    )
else:
    nearby = filter_companies(get_top(domaine), tailles, secteurs)
    spontaneous = rank_spontaneous(nearby, None, None, None, contrat, weights, show_liquidation)
if not spontaneous.empty:
    spontaneous = add_p_reponse(spontaneous, domaine, contrat, get_coefficients())
    # T26 (D36) : offres publiées par les autres sociétés du même groupe (familles de marque) ;
    # signalées seulement (« Groupe … : N offres »), jamais masquées : tout reste sur la carte.
    spontaneous = mark_family_offers(spontaneous, get_families(domaine), contrat)
    # T80 : correspondance CV ↔ entreprise, à part du score (rien ne change sans compétences)
    profile = get_skill_profile(domaine) if competences else None
    if profile is not None and match_skills(competences):
        # T83 : les compétences tapées à la main comptent si on les reconnaît (« SQL Server »)
        spontaneous = add_match(spontaneous, match_skills(competences), profile)
    elif competences and not spontaneous.empty:
        # T87 : compétences indiquées mais aucune reconnue → le dire (liste, carte, fiche)
        spontaneous = spontaneous.assign(correspondance_info=NO_MATCH_MESSAGE)
    sort_col = {TRI_P: "p_reponse", TRI_MATCH: "correspondance"}.get(tri)
    if sort_col in spontaneous and spontaneous[sort_col].notna().any():
        spontaneous = spontaneous.sort_values(
            [sort_col, "score"], ascending=False, na_position="last"
        ).reset_index(drop=True)

# T57 : sites d'une même entreprise (SIREN) dans le rayon → « +N » ; option une ligne par entreprise
if not spontaneous.empty:
    siren = spontaneous["siren"] if "siren" in spontaneous else spontaneous["siret"].str[:9]
    spontaneous = spontaneous.assign(_siren=siren.astype(str))
    n_same = spontaneous.groupby("_siren")["siret"].transform("size")
    spontaneous = spontaneous.assign(_autres_sites=n_same - 1)
    if une_par_entreprise:
        spontaneous = spontaneous.drop_duplicates("_siren").reset_index(drop=True)
    # T65 (D32) : palier de priorité en mots et en couleurs, parmi les résultats affichés.
    spontaneous = add_tiers(spontaneous)

# T76 : candidatures de la recherche en cours, pour les fiches (site ou entreprise) ouvertes
# depuis la recherche d'entreprises ou la liste des sites
if place is not None:
    st.session_state["_candidatures"] = spontaneous
    st.session_state["_candidatures_ctx"] = {"lieu": place.label, "rayon": rayon}
else:
    st.session_state.pop("_candidatures", None)
    st.session_state.pop("_candidatures_ctx", None)


# ------------------------------------------------------------------ résultat
contrat_txt = {
    "Tous": "",
    "Stage": " en stage",
    "Alternance": " en alternance",
    "Emploi": " en emploi",
}[contrat]
with right:
    # T57 : entreprises (SIREN distincts) et sites ; les sites masqués par l'option comptent aussi
    n_ent = spontaneous["_siren"].nunique() if not spontaneous.empty else 0
    if une_par_entreprise and not spontaneous.empty:
        n_sites = int(spontaneous["_autres_sites"].add(1).sum())
    else:
        n_sites = len(spontaneous)
    n_off = len(view)
    n_prio = int((spontaneous.get("palier", pd.Series(dtype=int)) == 1).sum())
    if place is not None:
        st.caption(f"Autour de **{place.label}** · {rayon} km{contrat_txt}")
    else:
        st.caption(
            f"**Partout en France**{contrat_txt} · les {fmt_int(len(spontaneous))} meilleures "
            "entreprises. Choisis ta ville pour voir celles qui sont proches de toi."
        )
    tiles = [
        Tile(
            fmt_int(n_ent),
            f"{_pl(n_ent, 'entreprise')} à démarcher sans offre publiée"
            + (f" ({fmt_int(n_sites)} sites)" if n_sites != n_ent else ""),
            ORANGE,
            "🏢",
        ),
        Tile(
            fmt_int(n_off),
            f"{_pl(n_off, 'offre')} {'publiées' if n_off > 1 else 'publiée'}",
            BLUE,
            "📄",
        ),
        Tile(
            fmt_int(n_prio),
            f"{_pl(n_prio, 'cible')} {'prioritaires' if n_prio > 1 else 'prioritaire'}",
            GREEN,
            "🎯",
        ),
    ]
    # T93 (essai) : correspondance forte avec le CV, distance médiane
    if (
        "correspondance_palier" in spontaneous
        and spontaneous["correspondance_palier"].notna().any()
    ):
        n_forte = int((spontaneous["correspondance_palier"] == "Forte").sum())
        tiles.append(Tile(fmt_int(n_forte), "en correspondance forte avec ton CV", "#7048E8", "🧩"))
    if not spontaneous.empty and spontaneous["distance_km"].notna().any():
        d = float(spontaneous["distance_km"].median())
        tiles.append(
            Tile(f"{d:.1f} km".replace(".", ","), "distance médiane des cibles", "#1098AD", "📍")
        )
    kpi_tiles(tiles)
    if spontaneous.empty and not FILES["scores"].exists():
        st.caption("Équipe : `scores.parquet` manquant (lancer `scripts/build_all.py`).")
    temp_banner(PAGES_DIR / "mon_espace.py")  # favoris temporaires (anonyme, T54)
    if not (view.empty and spontaneous.empty):
        st_folium(
            build_map(view, spontaneous, place, rayon if place is not None else None),
            height=620,
            use_container_width=True,
            returned_objects=[],
        )

# ------------------------------------------------------------------ listes
tab_spont, tab_offers = st.tabs(
    [
        f":material/domain: Candidatures spontanées ({len(spontaneous)})",
        f":material/work: Offres ({len(view)})",
    ]
)
with tab_spont:
    if spontaneous.empty:
        st.write("Aucune entreprise trouvée : élargis le rayon ou retire des filtres.")
    else:
        # T71 : on n'affiche (et ne colore) que les premières lignes du classement. La mise en
        # couleur passe par le Styler de pandas, limité à 262 144 cellules : à Paris (20 km,
        # ~57 000 entreprises), la liste entière plantait. Les tuiles et la carte comptent tout.
        shown = spontaneous.head(MAX_LIST_ROWS).reset_index(drop=True)
        # « Établissement (Entreprise) » quand les deux noms diffèrent, sinon le nom seul.
        etab = shown.get("nom_etablissement", pd.Series(index=shown.index))
        nom = [
            f"{e} ({n})" if isinstance(e, str) and e and e != n else n
            for e, n in zip(etab, shown["nom"].astype(str), strict=True)
        ]
        fav = favorite_refs("entreprise")
        table = pd.DataFrame(
            {
                "★": shown["siret"].astype(str).isin(fav).map({True: "★", False: ""}),
                "Entreprise": nom,
                "Lieu": shown.get("commune"),
                "Distance": shown["distance_km"],
                "Autres sites": shown["_autres_sites"].map(lambda n: f"+{n}" if n > 0 else ""),
                # T73 : taille de l'entreprise entière (officielle) et taille du site (fourchettes
                # SIRENE) ; vide quand l'information manque
                "Taille entreprise": shown.get(
                    "tranche_entreprise_libelle", pd.Series(index=shown.index)
                ),
                "Taille site": shown.get("tranche_effectif", pd.Series(index=shown.index)).map(
                    tranche_display
                ),
                "Situation": shown.get("procedure_type", pd.Series(index=shown.index)).map(
                    SITUATION_COURTE
                ),
                # T29 (D27) : ✔ si La Bonne Boîte signale l'établissement comme recruteur
                "La Bonne Boîte": signaled_by_lbb(shown).map({True: "✔", False: ""}),
                # T26 (D36) : le groupe (même marque) publie déjà des offres du domaine
                "Groupe": [
                    f"{f} · {n} offre{'s' if n > 1 else ''}" if n > 0 else ""
                    for f, n in zip(
                        shown.get("famille_nom", pd.Series(index=shown.index)),
                        shown.get("famille_offres", pd.Series(0, index=shown.index)).fillna(0),
                        strict=True,
                    )
                ],
                "Priorité": shown["palier_libelle"],
                "Score": shown["score"],
            }
        )
        # T64 : toujours affichée quand le modèle couvre le contrat et le domaine
        if "p_reponse" in shown and shown["p_reponse"].notna().any():
            table["Chance de réponse"] = shown["p_reponse"]
        # T80 : correspondance avec le CV, en paliers de mots (pourcentage dans la fiche) ;
        # T87 : juste après « Priorité », pour qu'on la voie sans faire défiler le tableau
        if "correspondance" in shown and shown["correspondance"].notna().any():
            pos = table.columns.get_loc("Priorité") + 1
            table.insert(pos, "Correspondance", shown["correspondance_palier"].to_numpy())
        elif "correspondance_info" in shown:
            st.info(NO_MATCH_MESSAGE, icon=":material/info:")
        if not table["Autres sites"].astype(bool).any():
            table = table.drop(columns="Autres sites")
        if not table["★"].astype(bool).any():
            table = table.drop(columns="★")
        if table["Distance"].isna().all():  # T93 : sans ville, pas de distance
            table = table.drop(columns="Distance")
        if table["Situation"].isna().all():
            table = table.drop(columns="Situation")
        if not table["La Bonne Boîte"].astype(bool).any():
            table = table.drop(columns="La Bonne Boîte")
        if not table["Groupe"].astype(bool).any():
            table = table.drop(columns="Groupe")
        version = st.session_state.get("_liste_version", 0)
        # T65 : couleur du palier sur la colonne « Priorité » (du plus foncé au gris).
        tier_colors = dict(zip(shown["palier_libelle"], shown["palier"], strict=True))
        styled = (
            table.style.map(  # T72 : le nom ressemble à un lien (clic → fiche)
                lambda _: LINK_STYLE, subset=["Entreprise"]
            )
            .map(
                lambda v: f"color: {tier_color(tier_colors.get(v))}; font-weight: 600",
                subset=["Priorité"],
            )
            .map(  # dégradé d'orange selon le score (clair → foncé)
                lambda v: (
                    f"background-color: {score_color(v)}; color: {text_color_on(score_color(v))}"
                    if pd.notna(v)
                    else ""
                ),
                subset=["Score"],
            )
        )
        if "Correspondance" in table:
            styled = styled.map(
                lambda v: f"color: {MATCH_COLORS.get(v, '#555')}; font-weight: 600",
                subset=["Correspondance"],
            )
        event = st.dataframe(
            styled,
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="single-cell",  # T72 : clic sur le nom (pas de case à cocher)
            key=f"liste_spont_{version}",
            column_config={
                "Entreprise": st.column_config.TextColumn(
                    help="Clique sur le nom pour ouvrir la fiche."
                ),
                "Distance": st.column_config.NumberColumn(format="%.1f km"),
                "Taille entreprise": st.column_config.TextColumn(
                    help="Salariés de toute l'entreprise, tous sites (fourchette SIRENE)."
                ),
                "Taille site": st.column_config.TextColumn(
                    help="Salariés de ce site (fourchette SIRENE, pas de nombre exact)."
                ),
                "Groupe": st.column_config.TextColumn(
                    help="Le groupe (même marque) publie déjà des offres pour ton contrat : "
                    "regarde-les aussi. Groupes reconnus par le nom (D36)."
                ),
                "Autres sites": st.column_config.TextColumn(
                    help="Autres sites de la même entreprise dans le rayon (voir sa fiche)."
                ),
                "Priorité": st.column_config.TextColumn(help=rule_text()),
                "Score": st.column_config.NumberColumn(
                    format="%.2f",
                    help="Moyenne pondérée des critères (0 à 1), d'où vient la priorité.",
                ),
                "Chance de réponse": st.column_config.NumberColumn(
                    format="percent", help=CHANCE_HELP
                ),
                "Correspondance": st.column_config.TextColumn(help=MATCH_HELP),
            },
        )
        more = len(spontaneous) - len(shown)
        st.caption(
            "Clique sur le nom d'une entreprise pour ouvrir sa fiche."
            + (
                f" Les {fmt_int(len(shown))} premières sur {fmt_int(len(spontaneous))} : "
                "réduis le rayon ou utilise les filtres pour affiner."
                if more > 0
                else ""
            )
        )
        cells = event.selection.cells if event is not None else []
        if cells and cells[0][1] == "Entreprise":
            r = shown.iloc[cells[0][0]]
            open_fiche(r["siret"], r, domaine)

with tab_offers:
    if view.empty:
        st.write("Aucune offre ne correspond à ta recherche.")
    else:
        ordered = view.sort_values("age_jours")
        fav_offers = favorite_refs("offre")
        table = ordered[
            ["titre", "entreprise_nom", "commune", "contrat", "niveaux_etudes", "age_jours", "url"]
        ].rename(
            columns={
                "titre": "Offre",
                "entreprise_nom": "Entreprise",
                "commune": "Lieu",
                "contrat": "Contrat",
                "niveaux_etudes": "Niveau",
                "age_jours": "Publiée il y a",
                "url": "Annonce",
            }
        )
        table["Niveau"] = table["Niveau"].map(levels_label)  # T67 : « Bac+5 », « Non précisé »
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


# ------------------------------------------------------------------ tableau de bord (T93)
dashboard(spontaneous)
