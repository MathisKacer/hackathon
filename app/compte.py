"""Bloc « compte » de la barre latérale (T48, D14).

Par défaut : mode démo anonyme, rien n'est enregistré. Connexion facultative pour retrouver
son profil (les réglages de recherche) d'une visite à l'autre.

Usage dans streamlit_app.py, AVANT de créer les widgets de recherche :

    with st.sidebar:
        account_sidebar({"contrat": ["Tous", "Stage", ...], "regions": all_regions, "query": None})
        st.radio("Contrat visé", [...], key="contrat")   # les widgets portent ces clés
        ...

Chaque clé du dictionnaire est la `key` d'un widget ; la valeur liste les options permises
(None = texte ou nombre libre). Les valeurs d'un profil qui ne sont plus permises sont ignorées.
"""

from __future__ import annotations

import streamlit as st

from radar import accounts

USER_KEY = "compte_user"  # {"id": int, "username": str} quand on est connecté
FAILS_KEY = "compte_echecs"
MAX_FAILS = 5  # tentatives de connexion par session


@st.cache_resource
def _con():
    return accounts.connect()


def current_user() -> dict | None:
    return st.session_state.get(USER_KEY)


def _sanitize(value, allowed):
    """Renvoie la valeur si elle est encore permise (listes filtrées), sinon None."""
    if allowed is None:
        return value
    if isinstance(value, list):
        return [v for v in value if v in allowed]
    return value if value in allowed else None


def _apply_profile(profile: dict, profile_keys: dict) -> None:
    for key, allowed in profile_keys.items():
        if key in profile:
            value = _sanitize(profile[key], allowed)
            if value is not None:
                st.session_state[key] = value


def _current_settings(profile_keys: dict) -> dict:
    return {k: st.session_state[k] for k in profile_keys if k in st.session_state}


def _log_in(user_id: int, username: str, profile_keys: dict) -> None:
    st.session_state[USER_KEY] = {"id": user_id, "username": username}
    st.session_state.pop(FAILS_KEY, None)
    _apply_profile(accounts.load_profile(_con(), user_id), profile_keys)
    st.rerun()


def _anonymous_box(profile_keys: dict) -> None:
    st.caption("🕶️ **Mode démo anonyme** : rien n'est enregistré.")
    with st.expander("Se connecter ou créer un compte"):
        tab_in, tab_up = st.tabs(["Connexion", "Créer un compte"])

        with tab_in, st.form("compte_connexion", clear_on_submit=True, border=False):
            username = st.text_input("Identifiant")
            password = st.text_input("Mot de passe", type="password")
            blocked = st.session_state.get(FAILS_KEY, 0) >= MAX_FAILS
            if st.form_submit_button("Se connecter", disabled=blocked, width="stretch"):
                user_id = accounts.authenticate(_con(), username, password)
                if user_id is None:
                    st.session_state[FAILS_KEY] = st.session_state.get(FAILS_KEY, 0) + 1
                    st.error("Identifiant ou mot de passe incorrect.")
                else:
                    _log_in(user_id, accounts.normalize_username(username), profile_keys)
            if blocked:
                st.warning("Trop de tentatives : recharge la page pour réessayer.")

        with tab_up, st.form("compte_creation", clear_on_submit=True, border=False):
            username = st.text_input("Identifiant", help="3 à 30 caractères : a-z, 0-9, . _ -")
            password = st.text_input(
                "Mot de passe", type="password", help=f"{accounts.PASSWORD_MIN} caractères min."
            )
            confirm = st.text_input("Confirmer le mot de passe", type="password")
            st.caption("Tes réglages actuels deviennent ton profil.")
            if st.form_submit_button("Créer mon compte", width="stretch"):
                if password != confirm:
                    st.error("Les deux mots de passe ne correspondent pas.")
                else:
                    try:
                        user_id = accounts.create_user(_con(), username, password)
                    except accounts.AccountError as e:
                        st.error(str(e))
                    else:
                        accounts.save_profile(_con(), user_id, _current_settings(profile_keys))
                        _log_in(user_id, accounts.normalize_username(username), profile_keys)


def _connected_box(user: dict, profile_keys: dict) -> None:
    st.markdown(f"👤 Connecté·e : **{user['username']}**")
    c1, c2 = st.columns(2)
    if c1.button("💾 Enregistrer", help="Enregistre tes réglages actuels", width="stretch"):
        accounts.save_profile(_con(), user["id"], _current_settings(profile_keys))
        st.toast("Profil enregistré.")
    if c2.button("Se déconnecter", width="stretch"):
        st.session_state.pop(USER_KEY, None)
        st.rerun()
    with st.expander("Supprimer mon compte"):
        st.caption("Efface définitivement ton compte et ton profil.")
        ok = st.checkbox("Je confirme la suppression", key="compte_confirm_suppr")
        if st.button("Supprimer", type="primary", disabled=not ok, width="stretch"):
            accounts.delete_user(_con(), user["id"])
            st.session_state.pop(USER_KEY, None)
            st.session_state.pop("compte_confirm_suppr", None)
            st.toast("Compte supprimé.")
            st.rerun()


def account_sidebar(profile_keys: dict[str, list | None]) -> dict | None:
    """Affiche le bloc compte ; renvoie l'utilisateur connecté, ou None en mode anonyme."""
    user = current_user()
    if user is not None and accounts.get_username(_con(), user["id"]) is None:
        st.session_state.pop(USER_KEY, None)  # compte supprimé ailleurs ou base réinitialisée
        user = None
    if user is None:
        _anonymous_box(profile_keys)
    else:
        _connected_box(user, profile_keys)
    return current_user()
