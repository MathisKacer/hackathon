"""T32 — Explication en une phrase de la recommandation d'une entreprise (couche orange).

`explain(row, contrat)` → « Recommandée car … ; … ; … » + une mise en garde éventuelle.

Les raisons sont tirées des colonnes déjà calculées (score T30, La Bonne Boîte T28, recruteurs
LBA T51, composantes de l'utilisateur T42) et **classées par leur apport au score**
(`apport_<composante>`) quand il est disponible : l'explication suit donc le classement et les
curseurs de l'utilisateur. Sans apports (score D13), un ordre fixe est utilisé.

Fonction pure, sans Streamlit : testable, et utilisée à la fois par la fiche (T43, @celia, via la
colonne `explication`) et par le popup de la carte.
"""

from __future__ import annotations

import pandas as pd

from radar.collect.sirene import TRANCHE_LIBELLES

MAX_REASONS = 3
LBB_SOURCE = "la_bonne_boite"
CONTRAT_LIBELLE = {"stage": "de stage", "alternance": "d'alternance", "emploi": "d'emploi"}
DOMAINE_LIBELLE = {"data": "data"}  # les autres domaines s'affichent tels quels


def _num(row, name: str) -> float | None:
    v = row.get(name)
    return float(v) if v is not None and pd.notna(v) else None


def _int(row, *names: str) -> int:
    for n in names:
        v = _num(row, n)
        if v is not None:
            return int(v)
    return 0


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'s' if n > 1 else ''}"


def reasons(row, contrat: str = "tous") -> list[tuple[str, str, float]]:
    """Raisons candidates : (composante liée, texte, priorité par défaut — plus petit = d'abord)."""
    contrat = contrat.lower()
    dom = DOMAINE_LIBELLE.get(str(row.get("domaine") or "data"), str(row.get("domaine")))
    out: list[tuple[str, str, float]] = []

    n_dom = _int(row, "n_offres_domaine_siren", "n_offres_domaine")
    n_stage = _int(row, "n_stage_domaine_siren", "n_stage_domaine")
    n_alt = _int(row, "n_alternance_domaine_siren", "n_alternance_domaine")
    if n_dom > 0 and contrat in CONTRAT_LIBELLE:
        # Détail des offres du domaine par type de contrat (sans répéter « dont 1 emploi »)
        parts = {"emploi": n_dom - n_stage - n_alt, "stage": n_stage, "alternance": n_alt}
        parts = {k: v for k, v in parts.items() if v > 0}
        if len(parts) == 1:
            ((k, v),) = parts.items()
            mot = {"emploi": "offre d'emploi", "stage": "offre de stage",
                   "alternance": "offre d'alternance"}[k]  # fmt: skip
            detail = f"{_plural(v, 'offre')}{mot[5:]} en ligne" if v > 1 else f"1 {mot} en ligne"
        else:
            detail = f"{_plural(n_dom, 'offre')} en ligne : " + ", ".join(
                _plural(v, k) for k, v in parts.items()
            )
        out.append(
            (
                "c_cachee",
                f"elle recrute des profils {dom} ({detail}) "
                f"mais ne propose aucune offre {CONTRAT_LIBELLE[contrat]}",
                0,
            )
        )

    if row.get("c_embauche_source") == LBB_SOURCE:
        out.append(
            (
                "c_embauche",
                f"La Bonne Boîte (France Travail) la signale comme susceptible d'embaucher "
                f"sur un métier {dom}",
                2,
            )
        )
    if bool(row.get("recruteur_lba")) and contrat in ("alternance", "tous"):
        out.append(
            (
                "c_recruteur_lba",
                "La bonne alternance la repère comme recruteur d'alternants sans offre publiée",
                3,
            )
        )

    c_int = _num(row, "c_intensite")
    if c_int is not None and c_int >= 0.5:
        top = max(1, round((1 - c_int) * 100))
        secteur = row.get("naf_libelle")
        sect = f" ({str(secteur).lower()})" if isinstance(secteur, str) and secteur else ""
        if n_dom == 0:
            txt = f"son secteur{sect} recrute beaucoup de profils {dom}"
        else:
            txt = f"son besoin {dom}, rapporté à sa taille, est"
            txt += " parmi les plus élevés" if top <= 10 else " élevé"
        out.append(("c_intensite", f"{txt} (top {top} % des entreprises)", 4))

    c_emb = _num(row, "c_embauche")
    if row.get("c_embauche_source") != LBB_SOURCE and c_emb is not None and c_emb >= 0.8:
        tranche = TRANCHE_LIBELLES.get(str(row.get("tranche_effectif") or ""))
        taille = f"établissement de {tranche}" if tranche else "établissement de bonne taille"
        out.append(
            ("c_embauche", f"{taille}, avec un besoin de recrutement {dom} attendu élevé", 5)
        )

    d = _num(row, "distance_km")
    if d is not None and d <= 5:
        out.append(("c_proximite", f"à {d:.1f} km de chez toi".replace(".", ","), 6))
    return out


def caveat(row) -> str | None:
    """Mise en garde sur le niveau de preuve (une phrase), ou None."""
    couverture = _num(row, "couverture")
    if couverture is not None and couverture == 0:
        return (
            "Estimation par secteur seulement : "
            "les offres de sa région ne sont pas encore collectées."
        )
    return None


def explain(row, contrat: str = "tous") -> str:
    """Phrase « Recommandée car … » pour une entreprise de la couche orange.

    `row` : une ligne (pd.Series ou dict) issue de `rank_spontaneous`."""
    cands = reasons(row, contrat)

    def weight(c: tuple[str, str, float]) -> tuple[int, float, float]:
        # L'opportunité cachée d'abord : c'est la raison même d'être dans la couche orange.
        # Puis par apport au score décroissant (suit les curseurs), sinon ordre par défaut.
        apport = _num(row, f"apport_{c[0]}")
        return (0 if c[0] == "c_cachee" else 1, -(apport if apport is not None else -1.0), c[2])

    chosen = sorted(cands, key=weight)[:MAX_REASONS]
    if chosen:
        txt = "Recommandée car " + " ; ".join(t for _, t, _ in chosen) + "."
    else:
        txt = "Recommandée d'après le besoin estimé de son secteur et sa taille."
    note = caveat(row)
    return f"{txt} {note}" if note else txt


MAX_EXPLAINED = 1000  # la carte en montre 300 ; au-delà, la fiche affiche la décomposition


def add_explanations(
    df: pd.DataFrame, contrat: str = "tous", limit: int = MAX_EXPLAINED
) -> pd.DataFrame:
    """Ajoute la colonne `explication` (lue par la fiche T43 et le popup de la carte).

    Seulement pour les `limit` premières lignes (df déjà trié) : sur un rayon de 50 km autour
    de Paris (~77 000 entreprises), tout expliquer coûterait plusieurs secondes à chaque clic.
    Les suivantes restent à None ; `explain(row)` peut être appelée à la demande."""
    out = df.copy()
    out["explication"] = None
    if len(out):
        head = out.head(limit)
        out.loc[head.index, "explication"] = [explain(r, contrat) for r in head.to_dict("records")]
    return out
