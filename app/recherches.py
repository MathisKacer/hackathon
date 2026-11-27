"""Recherches enregistrées (T84) : bouton sur Explorer, liste dans Mon espace.

On garde les **réglages** de la recherche (ville, rayon, domaine, contrat, filtres, poids,
classement, compétences), jamais les entreprises ni les résultats.
- Connecté : base des comptes (radar/accounts.py, table `recherches_enregistrees`).
- Sans compte : gardées le temps de la visite (`st.session_state`, rien sur le disque) et
  enregistrées à la connexion (compte._flush_temp_searches), comme les favoris (T54).
Au maximum accounts.SAVED_SEARCH_MAX recherches.
"""

from __future__ import annotations

from datetime import UTC, datetime

import streamlit as st
from commun import DOMAINS, TRI_P, WEIGHT_KEYS
from compte import TEMP_SEARCHES_KEY, TZ, _con, _current_settings, _relaunch_and_go, current_user

from radar import accounts
from radar.spontaneous import DEFAULT_WEIGHTS


def _temp() -> list[dict]:
    return st.session_state.setdefault(TEMP_SEARCHES_KEY, [])


def saved_searches() -> list[dict]:
    user = current_user()
    if user is not None:
        return accounts.list_saved_searches(_con(), user["id"])
    return list(reversed(_temp()))


def save(name: str, params: dict) -> bool:
    """False si déjà enregistrée ; AccountError au-delà du maximum."""
    user = current_user()
    if user is not None:
        return accounts.save_search(_con(), user["id"], name, params)
    temp = _temp()
    if any(s["params"] == params for s in temp):
        return False
    if len(temp) >= accounts.SAVED_SEARCH_MAX:
        raise accounts.AccountError(accounts.SAVED_SEARCH_FULL)
    next_id = max((s["id"] for s in temp), default=0) + 1
    temp.append({"id": next_id, "nom": name, "params": params, "created_at": datetime.now(UTC)})
    return True


def delete(search_id: int) -> None:
    user = current_user()
    if user is not None:
        accounts.delete_saved_search(_con(), user["id"], search_id)
    else:
        st.session_state[TEMP_SEARCHES_KEY] = [s for s in _temp() if s["id"] != search_id]


def default_name(params: dict) -> str:
    """« Stage · Data · Rennes (20 km) »."""
    contrat = params.get("contrat", "Tous")
    bits = ["Tous contrats" if contrat == "Tous" else contrat]
    domaine = params.get("domaine")
    if domaine in DOMAINS:
        bits.append(DOMAINS[domaine].label.split(",")[0])  # « Data », pas le libellé complet
    ville = str(params.get("ville") or "").split(" (")[0]
    if ville:
        bits.append(f"{ville} ({params.get('rayon')} km)")
    return " · ".join(bits)


def describe(params: dict, name: str = "") -> str:
    """Résumé court : la recherche (sauf si c'est déjà le nom) puis les seuls réglages
    différents de ceux par défaut. Vide s'il n'y a rien de plus que le nom."""
    base = default_name(params)
    bits = [] if name == base else [base]
    if params.get("query"):
        bits.append(f"mot-clé « {params['query']} »")
    if params.get("max_age", 60) != 60:
        bits.append(f"offres de moins de {params['max_age']} jours")
    for key, label in (("tailles", "taille"), ("secteurs", "secteur"), ("niveaux", "niveau")):
        if n := len(params.get(key) or []):
            bits.append(f"filtre {label} ({n})")
    if params.get("une_par_entreprise"):
        bits.append("une ligne par entreprise")
    if params.get("show_liquidation"):
        bits.append("avec liquidations")
    if params.get("tri") == TRI_P:
        bits.append("classement par chance de réponse")
    if any(params.get(k, DEFAULT_WEIGHTS[c]) != DEFAULT_WEIGHTS[c] for c, k in WEIGHT_KEYS.items()):
        bits.append("importance des critères modifiée")
    if skills := params.get("competences"):
        bits.append(f"{len(skills)} compétence{'s' if len(skills) > 1 else ''}")
    return " · ".join(bits)


def save_button(profile_keys: dict) -> None:
    """Explorer : « ☆ Enregistrer cette recherche », avec un nom facultatif."""
    with st.popover("Enregistrer cette recherche", icon=":material/bookmark_add:"):
        with st.form("enregistrer_recherche", clear_on_submit=True, border=False):
            params = _current_settings(profile_keys)
            name = st.text_input("Nom (facultatif)", placeholder=default_name(params))
            if st.form_submit_button("Enregistrer", type="primary", width="stretch"):
                try:
                    added = save(name.strip() or default_name(params), params)
                except accounts.AccountError as e:
                    st.error(str(e))
                else:
                    if not added:
                        st.info("Cette recherche est déjà enregistrée.")
                    elif current_user() is None:
                        st.success(
                            "Gardée le temps de ta visite. Crée un compte pour la conserver."
                        )
                    else:
                        st.success("Recherche enregistrée dans Mon espace.")


def saved_section(profile_keys: dict) -> None:
    """Mon espace : recherches enregistrées, avec « Relancer » et « Supprimer »."""
    searches = saved_searches()
    if not searches:
        st.write(
            "Aucune recherche enregistrée. Sur Explorer, lance une recherche puis clique sur "
            "« Enregistrer cette recherche »."
        )
        return
    note = "" if current_user() else " Sans compte, elles sont gardées le temps de ta visite."
    st.caption(f"{len(searches)} sur {accounts.SAVED_SEARCH_MAX}.{note}")
    for s in searches:
        with st.container(border=True, key=f"espace_recherche_{s['id']}"):
            left, b1, b2 = st.columns([4, 1, 1], vertical_alignment="center")
            left.markdown(f"**{s['nom']}**")
            date = s["created_at"].astimezone(TZ).strftime("%d/%m à %H:%M")
            details = describe(s["params"], s["nom"])
            left.caption((f"{details} · " if details else "") + f"enregistrée le {date}")
            b1.button(
                "Relancer",
                icon=":material/replay:",
                key=f"recherche_relancer_{s['id']}",
                on_click=_relaunch_and_go,
                args=(s["params"], profile_keys),
                width="stretch",
            )
            b2.button(
                "Supprimer",
                type="tertiary",
                icon=":material/delete:",
                key=f"recherche_supprimer_{s['id']}",
                on_click=delete,
                args=(s["id"],),
                width="stretch",
            )
