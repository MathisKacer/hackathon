"""Candidature spontanée **sans recherche** : ce qu'on peut dire d'une entreprise sans ville (T78).

    facts = candidature_facts(row, contrat="Stage", domaine_label="data", recruteur_lba=True,
                              groupe="Groupe Thales : 3 offres déjà publiées")
    # → {"verdict": "...", "lignes": ["...", ...]}

Sans ville choisie, il n'y a ni distance ni classement parmi les entreprises proches (palier,
D32), mais l'essentiel ne dépend pas du lieu : les offres déjà publiées pour le contrat visé
(au niveau de l'entreprise), le besoin dans le domaine (`c_intensite`, rang en France), le besoin
attendu du site (`c_embauche`), le signal « recruteur d'alternants » de La bonne alternance et le
groupe (familles de marque, D36).
"""

from __future__ import annotations

import duckdb
import pandas as pd

from radar.config import FILES

# « offre de stage », « offre d'alternance », « offre d'emploi »
CONTRACT_WORDS = {"stage": "de stage ", "alternance": "d'alternance ", "emploi": "d'emploi "}


def level_words(x) -> str | None:
    """Rang centile (0 à 1) → mots : « très élevé (plus que 92 % des entreprises) »."""
    if x is None or pd.isna(x):
        return None
    x = float(x)
    word = "très élevé" if x >= 0.9 else "élevé" if x >= 0.7 else "moyen" if x >= 0.4 else "faible"
    return f"{word} (plus que {round(100 * x)} % des entreprises)"


def _get(row, *names, default=0):
    for n in names:
        v = row.get(n) if hasattr(row, "get") else None
        if v is not None and not pd.isna(v):
            return v
    return default


def matching_offers(row, contrat: str) -> tuple[int, int]:
    """(offres du domaine pour le contrat visé, offres du domaine tous contrats), entreprise."""
    total = int(_get(row, "n_offres_domaine_siren", "n_offres_domaine"))
    stage = int(_get(row, "n_stage_domaine_siren", "n_stage_domaine"))
    alt = int(_get(row, "n_alternance_domaine_siren", "n_alternance_domaine"))
    c = contrat.lower()
    match = {"stage": stage, "alternance": alt, "emploi": max(total - stage - alt, 0)}.get(c, total)
    return match, total


def candidature_facts(
    row,
    contrat: str,
    domaine_label: str,
    recruteur_lba: bool | None = None,
    groupe: str = "",
    site_phrase: str = "de ce site",
) -> dict:
    """Verdict + lignes d'explication pour une fiche ouverte sans recherche."""
    c = contrat.lower()
    match, total = matching_offers(row, contrat)
    what = CONTRACT_WORDS.get(c, "")
    if match > 0:
        verdict = (
            f"L'entreprise publie déjà {match} offre{'s' if match > 1 else ''} {what}en "
            f"{domaine_label} : postule plutôt via ses offres (onglet Offres)."
        )
    elif total > 0:
        verdict = (
            f"Bonne cible : elle recrute en {domaine_label} ({total} offre"
            f"{'s' if total > 1 else ''}), mais aucune offre {what}publiée — c'est l'opportunité "
            "cachée."
        )
    else:
        verdict = (
            f"Candidature spontanée possible : aucune offre {what}publiée en {domaine_label} ; "
            "besoin estimé d'après le secteur et la taille."
        )
    lignes = []
    need = level_words(_get(row, "c_intensite", default=None))
    if need:
        lignes.append(f"Besoin en {domaine_label} : {need}.")
    hire = level_words(_get(row, "c_embauche", default=None))
    if hire:
        lignes.append(f"Besoin attendu {site_phrase} (selon sa taille) : {hire}.")
    if recruteur_lba and c in ("alternance", "tous"):
        lignes.append(
            "Signalée par La bonne alternance comme recruteur potentiel d'alternants sur un "
            f"métier {domaine_label}, sans offre publiée."
        )
    if groupe:
        lignes.append(f"{groupe} — regarde aussi ses offres.")
    return {"verdict": verdict, "lignes": lignes}


def load_company_scores(siren: str, domaine: str, path=None) -> pd.DataFrame:
    """Scores du domaine de tous les sites d'une entreprise, meilleur besoin attendu d'abord."""
    path = path or FILES["scores"]
    if not path.exists():
        return pd.DataFrame()
    cols = {r[0] for r in duckdb.connect().execute(f"DESCRIBE SELECT * FROM '{path}'").fetchall()}
    if "siren" in cols:
        where, args = "siren = ?", [str(siren)]
    else:  # scores factices : pas de colonne siren
        where, args = "substr(CAST(siret AS VARCHAR), 1, 9) = ?", [str(siren)]
    df = (
        duckdb.connect()
        .execute(f"SELECT * FROM '{path}' WHERE {where} AND domaine = ?", [*args, domaine])
        .df()
    )
    return df.sort_values("c_embauche", ascending=False) if "c_embauche" in df else df
