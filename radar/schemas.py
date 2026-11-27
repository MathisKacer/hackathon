"""Colonnes attendues des fichiers échangés entre modules.

Copie en code du tableau « Données et formats intermédiaires » de docs/ARCHITECTURE.md.
Si un schéma change : mettre à jour CE fichier ET le tableau, puis prévenir l'équipe.

Usage (dans un test ou en fin de pipeline) :
    from radar.schemas import check_columns
    check_columns(df, "entreprises")
"""

from __future__ import annotations

import pandas as pd

OFFRES_RAW = [
    "source",
    "offre_id",
    "date_collecte",
    "date_publication",
    "titre",
    "description",
    "entreprise_nom",
    "commune",
    "code_postal",
    "lat",
    "lon",
    "contrat_brut",
    "code_rome",
    "url",
    "siret",  # renseigné seulement si la source le fournit (La bonne alternance)
]

SCHEMAS: dict[str, list[str]] = {
    "offres_raw": OFFRES_RAW,
    "offres": OFFRES_RAW + ["domaine", "contrat", "siret_match", "match_score", "match_methode"],
    "entreprises": [
        "siret",
        "siren",
        "nom",
        "naf",
        "naf_libelle",
        "tranche_effectif",
        "categorie",
        "lat",
        "lon",
        "commune",
        "ca_n",
        "ca_n_1",
        "procedure_collective",
        "lbb_proba",
    ],
    # Une ligne par (siret, domaine). Les composantes c_* sont dans [0, 1].
    "scores": [
        "siret",
        "domaine",
        "c_intensite",
        "c_dynamisme",
        "c_embauche",
        "n_offres",
        "n_offres_domaine",
        "n_stage_domaine",
        "n_alternance_domaine",
        "intensite_post",
        "intensite_ic_bas",
        "intensite_ic_haut",
    ],
    # Données SIMULÉES (D6) : toujours l'indiquer dans l'app et les slides.
    "candidatures_simulees": [
        "siret",
        "profil_id",
        "domaine",
        "contrat_vise",
        "distance_km",
        "p_vraie",
        "repondu",
    ],
    "p_reponse": ["siret", "domaine", "contrat_vise", "p_reponse"],
}

CONTRATS = ("stage", "alternance", "emploi")


def check_columns(df: pd.DataFrame, name: str) -> None:
    """Lève une erreur si des colonnes du contrat manquent (les colonnes en plus sont permises)."""
    missing = [c for c in SCHEMAS[name] if c not in df.columns]
    if missing:
        raise ValueError(f"{name} : colonnes manquantes {missing} (voir docs/ARCHITECTURE.md)")
