"""Situation des entreprises (BODACC, T23, D24) : alerte et pénalité dans la couche orange.

Aucune entreprise n'est supprimée des données. Dans la couche orange :
- le score est multiplié par un coefficient qui dépend de la situation ET du contrat visé
  (une alternance ou un emploi engage bien plus l'entreprise qu'un stage) ;
- une alerte (drapeau + phrase) est affichée ;
- les entreprises en liquidation sont masquées par défaut (case à cocher pour les afficher).

Pour régler les pénalités : modifier PENALTIES ci-dessous (1 = aucune pénalité).
"""

from __future__ import annotations

import pandas as pd

# Coefficient appliqué au score, par situation et par contrat visé.
PENALTIES: dict[str, dict[str, float]] = {
    #               stage  alternance  emploi  tous
    "sauvegarde": {"stage": 0.85, "alternance": 0.75, "emploi": 0.75, "tous": 0.8},
    "plan": {"stage": 0.85, "alternance": 0.75, "emploi": 0.75, "tous": 0.8},
    "redressement": {"stage": 0.6, "alternance": 0.4, "emploi": 0.4, "tous": 0.5},
    "liquidation": {"stage": 0.1, "alternance": 0.05, "emploi": 0.05, "tous": 0.05},
}

# Drapeau et phrase affichés dans la liste et la fiche.
ALERTS: dict[str, tuple[str, str]] = {
    "sauvegarde": ("🟡", "Procédure de sauvegarde en cours : difficultés, activité maintenue"),
    "plan": ("🟡", "Sous plan de sauvegarde ou de redressement : l'entreprise poursuit"),
    "redressement": ("🟠", "En redressement judiciaire : activité sous contrôle du tribunal"),
    "liquidation": ("🔴", "En liquidation judiciaire : activité en principe arrêtée"),
}


def penalty(procedure_type: str | None, contrat: str) -> float:
    """Coefficient (≤ 1) pour une situation et un contrat visé ; 1 si pas de procédure."""
    table = PENALTIES.get(procedure_type or "")
    if table is None:
        return 1.0
    return table.get(contrat.lower(), table["tous"])


def alert_text(procedure_type: str | None, procedure_date=None) -> str:
    """« 🟠 En redressement judiciaire … (depuis 03/2026) » ; chaîne vide si rien à signaler."""
    if procedure_type not in ALERTS:
        return ""
    flag, text = ALERTS[procedure_type]
    when = pd.to_datetime(procedure_date, errors="coerce")
    return f"{flag} {text}" + (f" (depuis {when:%m/%Y})" if pd.notna(when) else "")


def apply_procedures(
    df: pd.DataFrame, contrat: str = "tous", show_liquidation: bool = False
) -> pd.DataFrame:
    """Pénalise `score`, ajoute `coef_procedure` et `alerte`, masque les liquidations par défaut.

    Sans colonne `procedure_type` (données factices, BODACC pas encore intégré) : ne fait rien
    d'autre qu'ajouter `coef_procedure = 1` et `alerte = ""`.
    """
    out = df.copy()
    if "procedure_type" not in out.columns or out.empty:
        return out.assign(coef_procedure=1.0, alerte="")
    if not show_liquidation:
        out = out[out["procedure_type"].ne("liquidation")]
    out["coef_procedure"] = out["procedure_type"].map(lambda t: penalty(t, contrat))
    if "score" in out.columns:
        out["score"] = out["score"] * out["coef_procedure"]
    dates = out["procedure_date"] if "procedure_date" in out.columns else None
    out["alerte"] = [
        alert_text(t, dates.iloc[i] if dates is not None else None)
        for i, t in enumerate(out["procedure_type"])
    ]
    return out
