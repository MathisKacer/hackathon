"""Page « Entreprises » : chercher une entreprise (nom, SIREN ou SIRET) et ouvrir sa fiche.

Cherche dans tout le référentiel (~406 000 établissements d'au moins 10 salariés), avec des
fautes de frappe tolérées (radar/recherche.py). Clic sur une ligne → fiche en fenêtre (T43).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from fiche_ui import open_fiche

from radar.recherche import load_index, search_companies

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


st.title("Entreprises")
st.caption("Cherche une entreprise pour voir sa fiche : activité, taille, offres, situation.")

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

etab = hits["nom_etablissement"]
names = [
    f"{e} ({n})" if isinstance(e, str) and e and e != n else n
    for e, n in zip(etab, hits["nom"].astype(str), strict=True)
]
table = pd.DataFrame(
    {
        "Entreprise": names,
        "Lieu": hits["commune"].fillna("") + " " + hits["code_postal"].fillna("").astype(str),
        "Taille": hits["tranche_libelle"],
        "Activité": hits["naf_libelle"],
        "Situation": hits["procedure_type"].map(SITUATION_COURTE),
    }
)
if table["Situation"].isna().all():
    table = table.drop(columns="Situation")

st.write(
    f"{len(hits)} établissement{'s' if len(hits) > 1 else ''}"
    + (" (les 50 plus proches de ta recherche)" if len(hits) == 50 else "")
    + " — clique sur une ligne pour ouvrir la fiche."
)
version = st.session_state.get("_liste_version", 0)
event = st.dataframe(
    table,
    hide_index=True,
    width="stretch",
    on_select="rerun",
    selection_mode="single-row",
    key=f"liste_entreprises_{version}",
)
rows = event.selection.rows if event is not None else []
if rows:
    open_fiche(hits.iloc[rows[0]]["siret"], None, st.session_state.get("domaine"))
