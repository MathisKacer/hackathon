"""Bloc « compte » de la barre latérale (T48) et historique des recherches (T49), D14.

Par défaut : mode démo anonyme, rien n'est enregistré. Connexion facultative pour retrouver
son profil (les réglages de recherche) d'une visite à l'autre.

Usage dans streamlit_app.py, AVANT de créer les widgets de recherche :

    with st.sidebar:
        account_sidebar({"contrat": ["Tous", "Stage", ...], "query": None})
        st.radio("Contrat visé", [...], key="contrat")   # les widgets portent ces clés
        ...

Chaque clé du dictionnaire est la `key` d'un widget ; la valeur liste les options permises
(None = texte ou nombre libre). Les valeurs d'un profil qui ne sont plus permises sont ignorées.

Les recherches enregistrées (T84) sont dans app/recherches.py ; elles remplacent
l'historique automatique (T49).
"""

from __future__ import annotations

from zoneinfo import ZoneInfo

import streamlit as st
from admin_ui import must_change_banner, password_change_box
from style import Stat, hero, profile_header, stat_bar

from radar import accounts

TEMP_FAVORITES_KEY = "_favoris_temporaires"  # favoris d'un visiteur anonyme (T54, app/favoris.py)
TEMP_SEARCHES_KEY = "_recherches_temporaires"  # visite anonyme (T84, app/recherches.py)
USER_KEY = "compte_user"  # {"id": int, "username": str} quand on est connecté
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


def _flush_temp_searches(user_id: int) -> tuple[int, int]:
    """Enregistre les recherches gardées pendant la visite anonyme (T84).

    Renvoie (enregistrées, non reprises parce que le maximum est atteint).
    """
    temp = st.session_state.pop(TEMP_SEARCHES_KEY, []) or []
    saved = lost = 0
    for s in temp:
        try:
            saved += accounts.save_search(
                _con(), user_id, s["nom"], s["params"], now=s["created_at"]
            )
        except accounts.AccountError:
            lost += 1
    return saved, lost


# T93 (essai) : page à ouvrir au prochain passage (lu par app/streamlit_app.py)
GO_PAGE_KEY = "_go_page"


def _log_in(user_id: int, username: str, profile_keys: dict) -> None:
    st.session_state[USER_KEY] = {"id": user_id, "username": username}
    _apply_profile(accounts.load_profile(_con(), user_id), profile_keys)
    n = _flush_temp_favorites(user_id)
    if n:
        st.session_state["_toast_favoris"] = n
    _, lost = _flush_temp_searches(user_id)
    if lost:
        st.session_state["_toast_recherches_perdues"] = lost
    st.rerun()


def _anonymous_box(profile_keys: dict) -> None:
    st.caption("🕶️ **Mode démo anonyme** : rien n'est enregistré.")
    with st.expander("Se connecter ou créer un compte"):
        login_forms(profile_keys)


def login_form(profile_keys: dict, go: str | None = None) -> None:
    """Formulaire « Se connecter » (T93 : page à part). `go` : page ouverte une fois connecté."""
    with st.form("compte_connexion", clear_on_submit=True, border=False):
        username = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("Se connecter", type="primary", width="stretch"):
            try:
                user_id = accounts.authenticate(_con(), username, password)
            except accounts.AccountLocked as e:
                until = e.until.astimezone(TZ).strftime("%H:%M")
                st.error(f"Trop de tentatives : compte bloqué jusqu'à {until}.")
            else:
                if user_id is None:
                    st.error("Identifiant ou mot de passe incorrect.")
                else:
                    if go:
                        st.session_state[GO_PAGE_KEY] = go
                    _log_in(user_id, accounts.normalize_username(username), profile_keys)


def signup_form(profile_keys: dict, go: str | None = None) -> None:
    """Formulaire « Créer un compte » (T93 : page « S'inscrire » à part)."""
    with st.form("compte_creation", clear_on_submit=True, border=False):
        username = st.text_input("Identifiant", help="3 à 30 caractères : a-z, 0-9, . _ -")
        password = st.text_input("Mot de passe", type="password", help=accounts.PASSWORD_RULES)
        confirm = st.text_input("Confirmer le mot de passe", type="password")
        st.caption(
            "**Ton mot de passe doit contenir :**\n"
            f"- au moins {accounts.PASSWORD_MIN} caractères\n"
            f"- au moins {accounts.PASSWORD_MIN_CATEGORIES} de ces 4 éléments : une minuscule, "
            "une majuscule, un chiffre, un caractère spécial (! ? @ # …)\n"
            "- ni ton identifiant, ni un mot de passe trop courant"
        )
        if st.form_submit_button("Créer mon compte", type="primary", width="stretch"):
            if password != confirm:
                st.error("Les deux mots de passe ne correspondent pas.")
            else:
                try:
                    user_id = accounts.create_user(_con(), username, password)
                except accounts.AccountError as e:
                    st.error(str(e))
                else:
                    accounts.save_profile(_con(), user_id, _current_settings(profile_keys))
                    if go:
                        st.session_state[GO_PAGE_KEY] = go
                    _log_in(user_id, accounts.normalize_username(username), profile_keys)


def login_forms(profile_keys: dict) -> None:
    """Onglets « Connexion » et « Créer un compte » (barre latérale des tests, ancienne page)."""
    tab_in, tab_up = st.tabs(["Connexion", "Créer un compte"])
    with tab_in:
        login_form(profile_keys)
    with tab_up:
        signup_form(profile_keys)


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


def _relaunch(params: dict, profile_keys: dict) -> None:
    # Rappel de bouton : exécuté avant que la page soit redessinée, donc avant la création des
    # widgets → on peut modifier leurs valeurs ici.
    _apply_profile(params, profile_keys)


# --- Version « pages » (Explorer enregistre, Mon espace affiche) ----------------------------

GO_EXPLORER_KEY = "_compte_aller_explorer"


def _validated_user() -> dict | None:
    user = current_user()
    if user is not None and accounts.get_username(_con(), user["id"]) is None:
        st.session_state.pop(USER_KEY, None)  # compte supprimé ailleurs ou base réinitialisée
        return None
    return user


def _relaunch_and_go(params: dict, profile_keys: dict) -> None:
    _apply_profile(params, profile_keys)
    # T93 (essai) : la page de résultats est ouverte par app/streamlit_app.py (GO_PAGE_KEY)
    st.session_state[GO_PAGE_KEY] = "recherche"


def _badges(values: list) -> str:
    """« Python », « SQL » → étiquettes Streamlit (markdown `:blue-badge[…]`)."""
    clean = (str(v).replace("[", "(").replace("]", ")") for v in values)
    return " ".join(f":blue-badge[{v}]" for v in clean)


def _profile_section(con, user: dict, saved_keys: dict, labels: dict, editor=None) -> None:
    """T81 : le profil = les réglages de `saved_keys` seulement (les compétences du CV).

    `editor` (T83, T86, facultatif) : `editor(profile, save)` affiche le profil et de quoi le
    modifier ; `save(valeurs)` l'enregistre **aussitôt** (plus de bouton « Enregistrer »).
    Sans `editor` : simple affichage, en étiquettes."""
    profile = {k: v for k, v in accounts.load_profile(con, user["id"]).items() if k in saved_keys}
    uid = user["id"]

    def save(values: dict) -> None:
        merged = {**profile, **{k: v for k, v in values.items() if k in saved_keys}}
        accounts.save_profile(_con(), uid, merged)
        profile.update(merged)

    for key in saved_keys:
        label = labels.get(key, key)
        st.subheader(f"Mes {label.lower()}" if key == "competences" else label)
        if editor is not None:
            continue
        saved = profile.get(key)
        if saved:
            st.markdown(_badges(saved) if isinstance(saved, list) else str(saved))
        else:
            st.caption("Rien d'enregistré.")
    if editor is not None:
        editor(profile, save)


def _delete_account_box(con, user: dict) -> None:
    with st.expander("Supprimer mon compte", icon=":material/warning:"):
        st.caption("Efface définitivement ton compte, ton profil et ton historique.")
        ok = st.checkbox("Je confirme la suppression", key="page_confirm_suppr")
        if st.button("Supprimer mon compte", type="primary", disabled=not ok):
            accounts.delete_user(con, user["id"])
            st.session_state.pop(USER_KEY, None)
            st.session_state.pop("page_confirm_suppr", None)
            st.toast("Compte supprimé.")
            st.rerun()


def _anonymous_page(saved_keys: dict, favorites_section, searches_section, keys: dict) -> None:
    """Sans compte (T93) : seulement le formulaire « Se connecter » (l'inscription a sa page)."""
    hero("Se connecter", "Ton compte garde tes compétences, tes favoris et tes recherches.")
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid, st.container(border=True, key="espace_connexion"):
        login_form(saved_keys, go="compte")


def account_page(
    profile_keys: dict[str, list | None],
    labels: dict[str, str] | None = None,
    explorer_page=None,
    favorites_section=None,
    saved_keys: dict[str, list | None] | None = None,
    candidatures_section=None,
    profile_editor=None,
    searches_section=None,
) -> None:
    """Page « Mon espace » : connexion, ou résumé chiffré + onglets (T85).

    Onglets : Mes candidatures, Mes favoris, Mes recherches, Mon profil. Leurs libellés ne
    contiennent pas de compteurs : un libellé qui change ramènerait au premier onglet.
    `profile_keys` : réglages d'une recherche (historique « Mes recherches », bouton Relancer).
    `saved_keys` (T81) : réglages gardés dans le **profil** (par défaut : tous) ; Radar n'y met
    que les compétences du CV. Ils sont restaurés à la connexion.
    `profile_editor` (T83, T86) : `editor(profile, save)`, affiche et modifie le profil ; chaque
    changement est enregistré aussitôt (`save`), sans bouton.
    `favorites_section`, `candidatures_section` : fonctions d'app/vues/mon_espace.py.
    """
    saved_keys = profile_keys if saved_keys is None else saved_keys
    labels = labels or {}
    if st.session_state.pop(GO_EXPLORER_KEY, False) and explorer_page is not None:
        st.switch_page(st.Page(explorer_page))
    user = _validated_user()
    if user is None:
        _anonymous_page(saved_keys, favorites_section, searches_section, profile_keys)
        return

    with st.container(key="page_compte"):  # T95 : même largeur de lecture que l'accueil
        _connected_page(
            user, profile_keys, labels, saved_keys, favorites_section,
            candidatures_section, searches_section, profile_editor,
        )  # fmt: skip


def _connected_page(
    user, profile_keys, labels, saved_keys, favorites_section,
    candidatures_section, searches_section, profile_editor,
) -> None:  # fmt: skip
    """Mon compte, une fois connecté : en-tête, chiffres, onglets."""
    con = _con()
    profile_header(user["username"], "Où en sont tes candidatures ?")
    _, right = st.columns([5, 1])
    if right.button("Se déconnecter", icon=":material/logout:", type="tertiary"):
        st.session_state.pop(USER_KEY, None)
        st.rerun()
    must_change_banner(con, user)  # T79 : mot de passe provisoire donné par un administrateur

    favs = accounts.list_favorites(con, user["id"])
    applied = [f for f in favs if f["candidate"]]
    interviews = sum(f["statut"] == "Entretien" for f in applied)
    n_due = sum(accounts.a_relancer(f) for f in applied)  # T90
    searches = accounts.list_saved_searches(con, user["id"])
    counts = (
        (len(applied), "candidature"),
        (interviews, "entretien"),
        (len(favs), "favori"),
        (len(searches), "recherche enregistrée"),
    )
    stats = [
        Stat(str(n), " ".join(w + ("s" if n > 1 else "") for w in words.split()))
        for n, words in counts
    ]
    if n_due:  # T90 : affiché seulement quand il y a quelque chose à faire
        stats.insert(0, Stat(str(n_due), "à relancer", alert=True))
    stat_bar(stats)

    names = [":material/send: Mes candidatures", ":material/star: Mes favoris"]
    names += [":material/history: Mes recherches", ":material/person: Mon profil"]
    tab_apply, tab_fav, tab_search, tab_profile = st.tabs(names)
    with tab_apply:
        if candidatures_section is not None:
            candidatures_section()
    with tab_fav:
        if favorites_section is not None:
            favorites_section()
    with tab_search:
        if searches_section is not None:
            searches_section(profile_keys)
    with tab_profile:
        with st.container(border=True, key="espace_profil"):
            _profile_section(con, user, saved_keys, labels, profile_editor)
        password_change_box(con, user)  # T79 (D39)
        _delete_account_box(con, user)
