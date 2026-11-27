"""Favoris (T54) : offres et entreprises, avec ou sans compte.

- Connecté : enregistrés dans la base des comptes (radar/accounts.py, table `favoris`).
- Anonyme : favoris **temporaires**, gardés dans `st.session_state` le temps de la visite
  (rien n'est écrit sur le disque, D14). À la connexion ou à la création du compte, ils sont
  enregistrés automatiquement (compte._log_in → flush_temp_favorites).

Références : offre → « source:offre_id » (offer_ref) ; entreprise → SIRET.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from compte import TEMP_FAVORITES_KEY, _con, current_user

from radar import accounts


def offer_ref(row: pd.Series) -> str:
    return f"{row.get('source')}:{row.get('offre_id')}"


def _temp() -> dict:
    return st.session_state.setdefault(TEMP_FAVORITES_KEY, {})


def favorite_refs(kind: str) -> set[str]:
    """Références des favoris d'un type (base si connecté, sinon temporaires)."""
    user = current_user()
    if user is not None:
        return accounts.favorite_refs(_con(), user["id"], kind)
    return {ref for (k, ref) in _temp() if k == kind}


def is_favorite(kind: str, ref: str) -> bool:
    return str(ref) in favorite_refs(kind)


def add(kind: str, ref: str, label: str, details: dict | None = None) -> None:
    user = current_user()
    if user is not None:
        try:
            accounts.add_favorite(_con(), user["id"], kind, str(ref), label, details)
        except accounts.AccountError as e:
            st.toast(str(e))
    else:
        _temp()[(kind, str(ref))] = {"label": label, "details": details or {}}


def remove(kind: str, ref: str) -> None:
    user = current_user()
    if user is not None:
        accounts.remove_favorite(_con(), user["id"], kind, str(ref))
    else:
        _temp().pop((kind, str(ref)), None)


def toggle(kind: str, ref: str, label: str, details: dict | None = None) -> None:
    if is_favorite(kind, ref):
        remove(kind, ref)
    else:
        add(kind, ref, label, details)


def favorites(kind: str | None = None) -> list[dict]:
    """Favoris au même format que accounts.list_favorites (temporaires : sans note ni case)."""
    user = current_user()
    if user is not None:
        return accounts.list_favorites(_con(), user["id"], kind)
    return [
        {
            "kind": k,
            "ref": ref,
            "label": v["label"],
            "details": v["details"],
            "note": "",
            "candidate": False,
            "created_at": None,
        }
        for (k, ref), v in reversed(list(_temp().items()))
        if kind is None or k == kind
    ]


def star_button(
    kind: str, ref: str, label: str, details: dict | None = None, key: str = ""
) -> None:
    """Bouton « ☆ Ajouter aux favoris » / « ★ Dans mes favoris »."""
    on = is_favorite(kind, ref)
    st.button(
        "★ Dans mes favoris" if on else "☆ Ajouter aux favoris",
        key=key or f"fav_{kind}_{ref}",
        on_click=toggle,
        args=(kind, ref, label, details),
        help="Retirer des favoris" if on else "Retrouve-la dans Mon espace",
        type="primary" if on else "secondary",
    )


def temp_banner(mon_espace_page=None) -> None:
    """Anonyme avec des favoris temporaires : invite à créer un compte pour les garder."""
    if current_user() is not None:
        return
    n = len(_temp())
    if not n:
        return
    with st.container(border=True):
        left, right = st.columns([4, 1], vertical_alignment="center")
        left.markdown(
            f"Tu as **{n} favori{'s' if n > 1 else ''} temporaire{'s' if n > 1 else ''}** : "
            "ils seront perdus en fermant la page. Crée un compte pour les garder."
        )
        if mon_espace_page is not None:
            right.page_link(st.Page(mon_espace_page), label="Créer un compte")


def sync_offers_editor(edited: pd.DataFrame, before: pd.DataFrame, offers: pd.DataFrame) -> bool:
    """Applique les cases ★ cochées / décochées dans la liste des offres. True si changement."""
    changed = edited["★"].astype(bool) != before["★"].astype(bool)
    for i in edited.index[changed]:
        r = offers.loc[i]
        label = f"{r.get('titre') or 'Offre'} — {r.get('entreprise_nom') or ''}".strip(" —")
        details = {
            k: (None if pd.isna(r.get(k)) else str(r.get(k)))
            for k in ("url", "commune", "contrat", "entreprise_nom", "date_publication")
        }
        if bool(edited.at[i, "★"]):
            add("offre", offer_ref(r), label, details)
        else:
            remove("offre", offer_ref(r))
    return bool(changed.any())
