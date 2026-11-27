"""Bloc « compte » de la barre latérale (T48) et historique des recherches (T49), D14.

Par défaut : mode démo anonyme, rien n'est enregistré. Connexion facultative pour retrouver
son profil (les réglages de recherche) d'une visite à l'autre.

Usage dans streamlit_app.py, AVANT de créer les widgets de recherche :

    with st.sidebar:
        account_sidebar({"contrat": ["Tous", "Stage", ...], "regions": all_regions, "query": None})
        st.radio("Contrat visé", [...], key="contrat")   # les widgets portent ces clés
        ...

Chaque clé du dictionnaire est la `key` d'un widget ; la valeur liste les options permises
(None = texte ou nombre libre). Les valeurs d'un profil qui ne sont plus permises sont ignorées.

Historique (T49), APRÈS le calcul des résultats :

    search_history(PROFILE_KEYS, n_results=len(view), top=[...], labels={"contrat": "Contrat"})

Ne fait rien en mode anonyme. Connecté : enregistre la recherche et affiche « Mes recherches »
en bas de la barre latérale, avec un bouton « Relancer » par recherche.
"""

from __future__ import annotations

from zoneinfo import ZoneInfo

import streamlit as st
from style import hero

from radar import accounts

TEMP_FAVORITES_KEY = "_favoris_temporaires"  # favoris d'un visiteur anonyme (T54, app/favoris.py)
USER_KEY = "compte_user"  # {"id": int, "username": str} quand on est connecté
HISTORY_SHOWN = 10
TZ = ZoneInfo("Europe/Paris")


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


def _flush_temp_favorites(user_id: int) -> int:
    """Enregistre dans le compte les favoris temporaires de la visite anonyme (T54)."""
    temp = st.session_state.pop(TEMP_FAVORITES_KEY, {}) or {}
    n = 0
    for (kind, ref), v in temp.items():
        try:
            accounts.add_favorite(_con(), user_id, kind, ref, v["label"], v.get("details"))
            n += 1
        except accounts.AccountError:
            break  # plafond atteint
    return n


def _log_in(user_id: int, username: str, profile_keys: dict) -> None:
    st.session_state[USER_KEY] = {"id": user_id, "username": username}
    _apply_profile(accounts.load_profile(_con(), user_id), profile_keys)
    n = _flush_temp_favorites(user_id)
    if n:
        st.session_state["_toast_favoris"] = n
    st.rerun()


def _anonymous_box(profile_keys: dict) -> None:
    st.caption("🕶️ **Mode démo anonyme** : rien n'est enregistré.")
    with st.expander("Se connecter ou créer un compte"):
        login_forms(profile_keys)


def login_forms(profile_keys: dict) -> None:
    """Onglets « Connexion » et « Créer un compte » (barre latérale ou page Mon espace)."""
    tab_in, tab_up = st.tabs(["Connexion", "Créer un compte"])

    with tab_in, st.form("compte_connexion", clear_on_submit=True, border=False):
        username = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("Se connecter", width="stretch"):
            try:
                user_id = accounts.authenticate(_con(), username, password)
            except accounts.AccountLocked as e:
                until = e.until.astimezone(TZ).strftime("%H:%M")
                st.error(f"Trop de tentatives : compte bloqué jusqu'à {until}.")
            else:
                if user_id is None:
                    st.error("Identifiant ou mot de passe incorrect.")
                else:
                    _log_in(user_id, accounts.normalize_username(username), profile_keys)

    with tab_up, st.form("compte_creation", clear_on_submit=True, border=False):
        username = st.text_input("Identifiant", help="3 à 30 caractères : a-z, 0-9, . _ -")
        password = st.text_input("Mot de passe", type="password", help=accounts.PASSWORD_RULES)
        confirm = st.text_input("Confirmer le mot de passe", type="password")
        st.caption(
            f"Au moins {accounts.PASSWORD_MIN} caractères, avec 3 types parmi "
            "minuscules, majuscules, chiffres et caractères spéciaux. "
            "Une phrase marche bien : « velo rouge 2026 Rennes »."
        )
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


# --- Historique des recherches (T49) -----------------------------------------------------


def _format_value(value) -> str:
    if isinstance(value, bool):
        return "oui" if value else "non"
    if isinstance(value, list):
        return ", ".join(map(str, value))
    return str(value)


def summarize(params: dict, labels: dict[str, str] | None = None) -> str:
    """Résumé lisible d'une recherche : « Contrat : Stage · Régions : Bretagne »."""
    labels = labels or {}
    parts = [
        f"{labels.get(k, k)} : {_format_value(v)}"
        for k, v in params.items()
        if v not in ("", [], None)
    ]
    return " · ".join(parts) or "réglages par défaut"


def _relaunch(params: dict, profile_keys: dict) -> None:
    # Rappel de bouton : exécuté avant que la page soit redessinée, donc avant la création des
    # widgets → on peut modifier leurs valeurs ici.
    _apply_profile(params, profile_keys)


def _clear_history(user_id: int) -> None:
    accounts.clear_searches(_con(), user_id)


def search_history(
    profile_keys: dict[str, list | None],
    n_results: int,
    top: list[str] | None = None,
    labels: dict[str, str] | None = None,
) -> None:
    """Connecté : enregistre la recherche en cours et affiche « Mes recherches »."""
    user = current_user()
    if user is None:
        return  # mode anonyme : rien n'est écrit
    con = _con()
    current_id = accounts.log_search(
        con, user["id"], _current_settings(profile_keys), n_results, top
    )
    searches = accounts.list_searches(con, user["id"], limit=HISTORY_SHOWN)
    with st.sidebar, st.expander(f"🕘 Mes recherches ({len(searches)})"):
        for s in searches:
            date = s["created_at"].astimezone(TZ).strftime("%d/%m à %H:%M")
            st.markdown(
                f"**{date}**{' · *en cours*' if s['id'] == current_id else ''}  \n"
                f"{summarize(s['params'], labels)}  \n"
                f"{s['n_resultats']} résultat(s)"
                + (f" · {', '.join(s['top_resultats'][:3])}" if s["top_resultats"] else "")
            )
            if s["id"] != current_id:
                st.button(
                    "↻ Relancer",
                    key=f"compte_relancer_{s['id']}",
                    on_click=_relaunch,
                    args=(s["params"], profile_keys),
                )
        st.button(
            "Effacer mon historique",
            key="compte_effacer_historique",
            on_click=_clear_history,
            args=(user["id"],),
            disabled=not searches,
        )


# --- Version « pages » (Explorer enregistre, Mon espace affiche) ----------------------------

GO_EXPLORER_KEY = "_compte_aller_explorer"


def _validated_user() -> dict | None:
    user = current_user()
    if user is not None and accounts.get_username(_con(), user["id"]) is None:
        st.session_state.pop(USER_KEY, None)  # compte supprimé ailleurs ou base réinitialisée
        return None
    return user


def record_search(
    profile_keys: dict[str, list | None], n_results: int, top: list[str] | None = None
) -> int | None:
    """Connecté : enregistre la recherche en cours (page Explorer). Anonyme : ne fait rien."""
    user = _validated_user()
    if user is None:
        return None
    return accounts.log_search(_con(), user["id"], _current_settings(profile_keys), n_results, top)


def _relaunch_and_go(params: dict, profile_keys: dict) -> None:
    _apply_profile(params, profile_keys)
    st.session_state[GO_EXPLORER_KEY] = True


def account_page(
    profile_keys: dict[str, list | None],
    labels: dict[str, str] | None = None,
    explorer_page=None,
    favorites_section=None,
) -> None:
    """Page « Mon espace » : connexion, ou profil + favoris + historique + suppression.

    `favorites_section` : fonction qui affiche « Mes favoris » (app/vues/mon_espace.py, T54).
    """
    if st.session_state.pop(GO_EXPLORER_KEY, False) and explorer_page is not None:
        st.switch_page(st.Page(explorer_page))
    user = _validated_user()
    if user is None:
        hero("Mon espace", "Ton compte, tes favoris et tes recherches.", compact=True)
        st.write(
            "Radar marche sans compte : rien n'est enregistré. Avec un compte, tes réglages "
            "et l'historique de tes recherches sont gardés d'une visite à l'autre."
        )
        left, _ = st.columns([1, 1])
        with left, st.container(border=True):
            login_forms(profile_keys)
        if favorites_section is not None:
            favorites_section()
        return

    hero(
        f"Bonjour {user['username']}", "Tes réglages, tes favoris et tes recherches.", compact=True
    )
    con = _con()
    c1, c2, _ = st.columns([1, 1, 2])
    if c1.button(
        "Enregistrer mes réglages",
        icon=":material/save:",
        type="primary",
        width="stretch",
        help="Ta recherche actuelle devient ton profil.",
    ):
        accounts.save_profile(con, user["id"], _current_settings(profile_keys))
        st.toast("Réglages enregistrés.")
    if c2.button("Se déconnecter", width="stretch", icon=":material/logout:"):
        st.session_state.pop(USER_KEY, None)
        st.rerun()
    profile = accounts.load_profile(con, user["id"])
    st.caption(
        "Profil enregistré : " + summarize(profile, labels)
        if profile
        else "Aucun profil enregistré pour l'instant."
    )

    if favorites_section is not None:
        favorites_section()

    st.subheader("Mes recherches")
    searches = accounts.list_searches(con, user["id"], limit=HISTORY_SHOWN)
    if not searches:
        st.write("Tes recherches apparaîtront ici.")
    for s in searches:
        with st.container(border=True):
            left, right = st.columns([5, 1], vertical_alignment="center")
            date = s["created_at"].astimezone(TZ).strftime("%d/%m à %H:%M")
            left.markdown(
                f"**{date}** · {s['n_resultats']} résultat(s)  \n"
                f"{summarize(s['params'], labels)}"
                + (f"  \n*{', '.join(s['top_resultats'][:3])}*" if s["top_resultats"] else "")
            )
            right.button(
                "Relancer",
                icon=":material/replay:",
                key=f"page_relancer_{s['id']}",
                on_click=_relaunch_and_go,
                args=(s["params"], profile_keys),
                width="stretch",
            )
    if searches:
        st.button("Effacer mon historique", on_click=_clear_history, args=(user["id"],))

    with st.expander("Supprimer mon compte"):
        st.caption("Efface définitivement ton compte, ton profil et ton historique.")
        ok = st.checkbox("Je confirme la suppression", key="page_confirm_suppr")
        if st.button("Supprimer mon compte", type="primary", disabled=not ok):
            accounts.delete_user(con, user["id"])
            st.session_state.pop(USER_KEY, None)
            st.session_state.pop("page_confirm_suppr", None)
            st.toast("Compte supprimé.")
            st.rerun()
