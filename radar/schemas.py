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
    # « Recruteurs potentiels » La bonne alternance : entreprises SANS offre publiée mais
    # susceptibles d'embaucher des alternants (signal d'opportunité cachée). Une ligne par SIRET.
    "recruteurs_lba": [
        "source",
        "recruteur_id",
        "date_collecte",
        "siret",
        "nom",
        "raison_sociale",
        "naf",
        "naf_libelle",
        "taille",
        "adresse",
        "code_postal",
        "commune",
        "lat",
        "lon",
        "site_web",
        "opco",
        "idcc",
        "code_rome",
        "url",
    ],
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

# offres.parquet APRÈS le rapprochement T21 (D10) : ce que l'app et le score peuvent utiliser.
# `intermediaire` = plateforme / cabinet / intérim (pas de SIRET, voulu) ; `siren_match` sert à
# exclure de la couche « candidature spontanée » les entreprises qui ont déjà une offre (D8).
SCHEMAS["offres_rapprochees"] = SCHEMAS["offres"] + [
    "siren_match",
    "match_confiance",
    "match_distance_km",
    "intermediaire",
]

CONTRATS = ("stage", "alternance", "emploi")


def check_columns(df: pd.DataFrame, name: str) -> None:
    """Lève une erreur si des colonnes du contrat manquent (les colonnes en plus sont permises)."""
    missing = [c for c in SCHEMAS[name] if c not in df.columns]
    if missing:
        raise ValueError(f"{name} : colonnes manquantes {missing} (voir docs/ARCHITECTURE.md)")


# scores.parquet RÉEL (T30, D13) : colonnes en plus du contrat, utilisées par l'app.
# `couverture` = part de l'effectif situé dans une région collectée (0 → score = a priori du
# secteur) ; `volume_suspect` → à écarter ; `n_offres_domaine_siren` → exclusion couche orange.
SCHEMAS["scores_reels"] = SCHEMAS["scores"] + [
    "siren",
    "couverture",
    "prior_moyenne",
    "besoin_attendu",
    "n_offres_domaine_siren",
    "n_stage_domaine_siren",
    "n_alternance_domaine_siren",
    "volume_suspect",
    "c_embauche_source",
    "c_dynamisme_disponible",
]

# Modèle de réponse RÉEL (T35/T36) : données SIMULÉES (D6), toujours signalées par
# `donnees_simulees`. `p_reponse` est calculée à distance nulle : l'app ajoute le terme de
# distance (coefficient dans data/processed/modele_reponse.json). Les contrib_* expliquent la fiche.
SCHEMAS["p_reponse_modele"] = SCHEMAS["p_reponse"] + [
    "donnees_simulees",
    "contrib_c_intensite",
    "contrib_c_embauche",
    "contrib_log10_effectif",
    "contrib_alternance",
    "contrib_a_offre_domaine",
]
