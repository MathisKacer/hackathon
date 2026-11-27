"""Page « Explorer » : où candidater autour de soi.

Recherche en haut (où, contrat, domaine, rayon) + bouton « Filtres » ; carte ; onglets
Candidatures spontanées / Offres ; clic sur une entreprise → fiche dans une fenêtre (T43).
Logique de classement inchangée : radar/spontaneous.py (T40, T41, T42, T23), T37, T51.
"""

from __future__ import annotations

import html

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
    profile_keys,
    reset_weights,
)
from compte import record_search
from favoris import favorite_refs, offer_ref, sync_offers_editor, temp_banner
from fiche_ui import open_fiche
from streamlit_folium import st_folium
from style import GREEN, LINK_STYLE, RED, Tile, fmt_int, hero, kpi_tiles, pill

from radar.collect.sirene import tranche_display
from radar.competences import MATCH_COLORS, SKILL_LABELS, add_match, detect_skills, pdf_text
from radar.familles import mark_family_offers
from radar.filters import SECTIONS, TAILLES, filter_companies
from radar.niveau import levels_label
from radar.paliers import (
    add_tiers,
    rule_text,
    score_color,
    text_color_on,
    tier_color,
    tier_text,
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


def _read_cv() -> None:
    """T45 : compétences lues dans le CV déposé, ajoutées à la liste « Tes compétences ».

    Le PDF reste en mémoire le temps de la lecture : rien n'est écrit sur le disque. Seule la
    liste des compétences est un réglage (enregistré dans le profil si on est connecté)."""
    fichier = st.session_state.get("cv_fichier")
    if fichier is None:
        return
    found = detect_skills(pdf_text(fichier.getvalue()))
    before = list(st.session_state.get("competences", []))
    st.session_state["competences"] = before + [s for s in found if s not in before]
    st.session_state["_cv_message"] = (
        f"{len(found)} compétence{'s' if len(found) > 1 else ''} trouvée"
        f"{'s' if len(found) > 1 else ''} dans ton CV. Tu peux corriger la liste."
        if found
        else "Aucune compétence reconnue : le PDF est peut-être une image scannée. "
        "Choisis tes compétences dans la liste."
    )


def _n_filters_on() -> int:
    """Nombre de filtres modifiés (affiché sur le bouton « Filtres »)."""
    ss = st.session_state
    return sum(
        [
            bool(str(ss.get("query", "")).strip()),
            ss.get("max_age", 60) != 60,
            not ss.get("only_data", True),
            bool(ss.get("tailles")),
            bool(ss.get("secteurs")),
            bool(ss.get("show_liquidation")),
            ss.get("tri") in (TRI_P, TRI_MATCH),
            bool(ss.get("une_par_entreprise")),
            bool(ss.get("niveaux")),
            bool(ss.get("competences")),
        ]
    )


offers = get_offers()
if offers.empty:
    st.title("Radar")
    st.info("Aucune offre n'est chargée pour le moment.")
    st.caption("Équipe : lancer la collecte ou récupérer `data/raw/offres_raw/` (voir CLAUDE.md).")
    st.stop()

PROFILE_KEYS = profile_keys()

# ------------------------------------------------------------------ recherche
hero(
    "Où candidater ?",
    "Les offres publiées autour de toi, et surtout les entreprises qui recrutent dans ton "
    "domaine sans avoir publié d'offre pour ton contrat : les meilleures cibles de candidature "
    "spontanée.",
)

with st.container(border=True, key="carte_recherche"):
    c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
    # Suggesteur de ville (T55) : on tape le début du nom (ou un code postal) et on choisit
    # « Ville (codes postaux) ». index=None : la croix permet d'effacer pour changer de ville.
    ville = c1.selectbox(
        "Où ?",
        get_communes()["label"].tolist(),
        index=None,
        key="ville",
        placeholder="Tape le nom de ta ville ou un code postal…",
    )
    contrat = c2.segmented_control("Contrat", CONTRATS, key="contrat", required=True) or "Tous"
    c3, c4, c5 = st.columns([3, 1, 1], vertical_alignment="bottom")
    domaine = c3.selectbox(
        "Domaine", DOMAINES, key="domaine", format_func=lambda k: DOMAINS[k].label
    )
    rayon = c4.selectbox("Rayon", RAYONS, key="rayon", format_func=lambda r: f"{r} km")
    n_on = _n_filters_on()
    with c5.popover(
        f"Filtres ({n_on})" if n_on else "Filtres", width="stretch", icon=":material/tune:"
    ):
        st.markdown("**Offres**")
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
        une_par_entreprise = st.checkbox(
            "Une ligne par entreprise",
            key="une_par_entreprise",
            help="Garde seulement le site le mieux classé de chaque entreprise "
            "(les autres sites restent visibles dans sa fiche).",
        )
        st.markdown("**Ton CV**")
        st.file_uploader(
            "Dépose ton CV (PDF)",
            type="pdf",
            key="cv_fichier",
            on_change=_read_cv,
            help="On y repère tes compétences (Python, SQL, comptabilité…) pour afficher ta "
            "correspondance avec chaque entreprise (sans changer le score). "
            "Ton CV n'est pas conservé.",
        )
        if msg := st.session_state.pop("_cv_message", None):
            st.caption(msg)
        competences = st.multiselect(
            "Tes compétences",
            SKILL_LABELS,
            key="competences",
            placeholder="Choisis ou dépose ton CV",
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
if place is not None:
    view = view[haversine_km(place.lat, place.lon, view["lat"], view["lon"]) <= rayon]
    nearby = filter_companies(
        get_nearby(place.lat, place.lon, float(rayon), domaine), tailles, secteurs
    )
    spontaneous = rank_spontaneous(
        nearby, place.lat, place.lon, rayon, contrat, weights, show_liquidation
    )
    spontaneous = add_p_reponse(spontaneous, domaine, contrat, get_coefficients())
    # T26 (D36) : offres publiées par les autres sociétés du même groupe (familles de marque) ;
    # signalées seulement (« Groupe … : N offres »), jamais masquées : tout reste sur la carte.
    spontaneous = mark_family_offers(spontaneous, get_families(domaine), contrat)
    # T80 : correspondance CV ↔ entreprise, à part du score (rien ne change sans compétences)
    profile = get_skill_profile(domaine) if competences else None
    if profile is not None:
        spontaneous = add_match(spontaneous, competences, profile)
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
    # Comment ça marche, en 3 cartes
    steps = [
        (":material/location_on:", "Choisis ta ville", "et le contrat que tu vises, en haut."),
        (
            ":material/map:",
            "Repère sur la carte",
            "Bleu : les offres en ligne. Orange : les entreprises qui recrutent dans ton domaine "
            + {
                "Stage": "mais n'ont publié aucune offre de stage",
                "Alternance": "mais n'ont publié aucune offre d'alternance",
                "Emploi": "mais n'ont publié aucune offre d'emploi",
            }.get(contrat, "sans offre en ligne")
            + " : à contacter directement.",
        ),
        (
            ":material/apartment:",
            "Ouvre une fiche",
            "pour savoir pourquoi l'entreprise est recommandée et préparer ta candidature.",
        ),
    ]
    for col, (n, (icon, title, text)) in zip(st.columns(3), enumerate(steps, 1), strict=True):
        with col.container(border=True, key=f"etape_{n}"):
            st.markdown(f"<span class='radar-step-n'>{n}</span>", unsafe_allow_html=True)
            st.markdown(f"**{icon} {title}**")
            st.caption(text)
else:
    # T57 : entreprises (SIREN distincts) et sites ; les sites masqués par l'option comptent aussi
    n_ent = spontaneous["_siren"].nunique() if not spontaneous.empty else 0
    if une_par_entreprise and not spontaneous.empty:
        n_sites = int(spontaneous["_autres_sites"].add(1).sum())
    else:
        n_sites = len(spontaneous)
    n_off = len(view)
    n_prio = int((spontaneous.get("palier", pd.Series(dtype=int)) == 1).sum())
    n_alert = (
        int(spontaneous["procedure_type"].notna().sum()) if "procedure_type" in spontaneous else 0
    )
    st.caption(f"Autour de **{place.label}** · {rayon} km{contrat_txt}")
    tiles = [
        Tile(
            fmt_int(n_ent),
            f"{_pl(n_ent, 'entreprise')} à démarcher sans offre publiée"
            + (f" ({fmt_int(n_sites)} sites)" if n_sites != n_ent else ""),
            ORANGE,
        ),
        Tile(
            fmt_int(n_off), f"{_pl(n_off, 'offre')} {'publiées' if n_off > 1 else 'publiée'}", BLUE
        ),
        Tile(
            fmt_int(n_prio),
            f"{_pl(n_prio, 'cible')} {'prioritaires' if n_prio > 1 else 'prioritaire'}",
            GREEN,
        ),
    ]
    if n_alert:
        tiles.append(Tile(fmt_int(n_alert), "en difficulté (signalées)", RED))
    kpi_tiles(tiles)
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

# ------------------------------------------------------------------ meilleures cibles
if place is not None and not spontaneous.empty:
    st.markdown("#### :material/workspace_premium: Les meilleures cibles")
    top = spontaneous.head(4)
    for col, (i, r) in zip(st.columns(len(top)), top.iterrows(), strict=True):
        with col.container(border=True, key=f"cible_{i}"):
            rank = r.get("palier")
            if pd.notna(rank):
                st.markdown(pill(tier_text(rank, False), tier_color(rank)), unsafe_allow_html=True)
            etab = r.get("nom_etablissement")
            name = (
                f"{etab} ({r['nom']})"
                if isinstance(etab, str) and etab and etab != r["nom"]
                else str(r["nom"])
            )
            sub_bits = [
                str(r.get("commune") or "").title(),
                f"{r['distance_km']:.1f} km",
                tranche_display(r.get("tranche_effectif")),
            ]
            sub_txt = " · ".join(b for b in sub_bits if b)
            st.markdown(
                f"<div class='radar-card-title'>{html.escape(name)}</div>"
                f"<div class='radar-card-sub'>{html.escape(sub_txt)}</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                "Voir la fiche",
                key=f"voir_cible_{i}",
                icon=":material/open_in_new:",
                width="stretch",
            ):
                open_fiche(r["siret"], r, domaine)

# ------------------------------------------------------------------ listes
tab_spont, tab_offers = st.tabs(
    [
        f":material/domain: Candidatures spontanées ({len(spontaneous)})",
        f":material/work: Offres ({len(view)})",
    ]
)
with tab_spont:
    if place is None:
        st.write("Choisis ta ville pour voir les entreprises à démarcher.")
    elif spontaneous.empty:
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
        # T80 : correspondance avec le CV, en paliers de mots (pourcentage dans la fiche)
        if "correspondance" in shown and shown["correspondance"].notna().any():
            table["Correspondance"] = shown["correspondance_palier"]
        if not table["Autres sites"].astype(bool).any():
            table = table.drop(columns="Autres sites")
        if not table["★"].astype(bool).any():
            table = table.drop(columns="★")
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
