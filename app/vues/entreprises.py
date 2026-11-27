"""Page « Entreprises » : chercher une entreprise (nom, SIREN ou SIRET) et ouvrir sa fiche.

Cherche dans tout le référentiel (~406 000 établissements d'au moins 10 salariés), avec des
fautes de frappe tolérées (radar/recherche.py). Clic sur une ligne → fiche en fenêtre (T43).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from fiche_ui import open_fiche
from style import LINK_STYLE, hero

from radar.collect.sirene import tranche_display
from radar.recherche import load_index, search_companies, with_companies

SITUATION_COURTE = {
    "sauvegarde": "🟡 Sauvegarde",
    "plan": "🟡 Plan",
    "redressement": "🟠 Redressement",
    "liquidation": "🔴 Liquidation",
}


@st.cache_resource(show_spinner="Préparation de la recherche…")
def _index() -> pd.DataFrame:
    return load_index()


@st.cache_data(show_spinner=False, max_entries=200)
def _search(query: str, commune: str) -> pd.DataFrame:
    return search_companies(_index(), query, commune, limit=50)


hero(
    "Entreprises",
    "Cherche une entreprise pour voir sa fiche : activité, taille, sites, offres, situation.",
    compact=True,
)

c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
query = c1.text_input(
    "Entreprise",
    key="recherche_entreprise",
    placeholder="Nom de l'entreprise, SIREN ou SIRET",
)
commune = c2.text_input("Ville ou code postal", key="recherche_commune", placeholder="Facultatif")

if not query.strip():
    st.write("Exemples : Orange, Crédit Agricole, Sopra Steria, Insee…")
    st.stop()

hits = _search(query.strip(), commune.strip())
if hits.empty:
    st.write(
        f"Aucune entreprise trouvée pour « {query} »"
        + (f" à « {commune} »" if commune.strip() else "")
        + ". Vérifie l'orthographe ou retire la ville."
    )
    st.caption("La recherche porte sur les établissements d'au moins 10 salariés.")
    st.stop()

# T57 : l'entreprise entière d'abord (une ligne par SIREN à plusieurs sites), puis les sites.
rows_all = with_companies(hits)
is_company = rows_all["_type"].eq("entreprise")
etab = rows_all["nom_etablissement"]
names = [
    f"{n} — toute l'entreprise"
    if comp
    else (f"{e} ({n})" if isinstance(e, str) and e and e != n else n)
    for comp, e, n in zip(is_company, etab, rows_all["nom"].astype(str), strict=True)
]
lieu = rows_all["commune"].fillna("") + " " + rows_all["code_postal"].fillna("").astype(str)
n_sites = rows_all["_n_sites"].fillna(1).astype(int)
table = pd.DataFrame(
    {
        "Entreprise": names,
        "Lieu": lieu.where(~is_company, n_sites.map(lambda n: f"{n} sites en France")),
        # T73 : fourchette du site ; pour l'entreprise entière, sa tranche officielle
        "Taille": rows_all["tranche_effectif"]
        .map(tranche_display)
        .where(~is_company, rows_all["tranche_entreprise_libelle"]),
        "Activité": rows_all["naf_libelle"],
        "Situation": rows_all["procedure_type"].map(SITUATION_COURTE),
    }
)
if table["Situation"].isna().all():
    table = table.drop(columns="Situation")

n_comp = int(is_company.sum())
st.write(
    (f"{n_comp} entreprise{'s' if n_comp > 1 else ''} et " if n_comp else "")
    + f"{len(hits)} site{'s' if len(hits) > 1 else ''}"
    + (" (les 50 plus proches de ta recherche)" if len(hits) == 50 else "")
    + " — clique sur un nom pour ouvrir la fiche."
)
version = st.session_state.get("_liste_version", 0)
event = st.dataframe(
    # T72 : le nom ressemble à un lien ; un clic sur le nom ouvre la fiche
    table.style.map(lambda _: LINK_STYLE, subset=["Entreprise"]),
    hide_index=True,
    width="stretch",
    on_select="rerun",
    selection_mode="single-cell",
    key=f"liste_entreprises_{version}",
    column_config={
        "Entreprise": st.column_config.TextColumn(help="Clique sur le nom pour ouvrir la fiche.")
    },
)
cells = event.selection.cells if event is not None else []
if cells and cells[0][1] == "Entreprise":
    r = rows_all.iloc[cells[0][0]]
    domaine = st.session_state.get("domaine")
    if r["_type"] == "entreprise":
        open_fiche(None, None, domaine, siren=r["siren"])
    else:
        open_fiche(r["siret"], None, domaine)
