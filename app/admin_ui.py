"""Gestion des comptes dans l'app (T79, D39) : changer son mot de passe ; page Administration.

La logique est dans `radar/admin.py`. Nommer un administrateur ne se fait **pas** ici : seulement
par `scripts/admin.py` dans le terminal du pod (membres de l'équipe).
"""

from __future__ import annotations

from zoneinfo import ZoneInfo

import streamlit as st

from radar import accounts, admin

TZ = ZoneInfo("Europe/Paris")
TEMP_KEY = "_admin_mdp_provisoire"  # {"username": …, "password": …}, affiché une seule fois


def must_change_banner(con, user: dict) -> None:
    """Après un mot de passe provisoire : inviter à le changer tout de suite."""
    if admin.must_change_password(con, user["id"]):
        st.warning(
            "Tu utilises un **mot de passe provisoire** donné par un administrateur : "
            "change-le dans l'onglet « Mon profil ».",
            icon=":material/key:",
        )


def password_change_box(con, user: dict) -> None:
    """« Changer mon mot de passe » (Mon espace), mêmes règles qu'à la création (D16)."""
    expanded = admin.must_change_password(con, user["id"])
    with st.expander("Changer mon mot de passe", expanded=expanded, icon=":material/key:"):
        with st.form("changer_mdp", clear_on_submit=True, border=False):
            old = st.text_input("Mot de passe actuel", type="password")
            new = st.text_input(
                "Nouveau mot de passe",
                type="password",
                help="Au moins 12 caractères et 3 types parmi minuscules, majuscules, "
                "chiffres et caractères spéciaux.",
            )
            again = st.text_input("Nouveau mot de passe (encore)", type="password")
            if st.form_submit_button("Changer mon mot de passe", type="primary"):
                if new != again:
                    st.error("Les deux nouveaux mots de passe ne sont pas identiques.")
                else:
                    try:
                        admin.change_password(con, user["id"], old, new)
                        st.success("Mot de passe changé.")
                    except accounts.AccountError as e:
                        st.error(str(e))


def admin_page(con, user: dict | None) -> None:
    """Page « Administration » : réservée aux administrateurs (revérifié à chaque affichage)."""
    if user is None or not admin.is_admin(con, user["id"]):
        st.error("Page réservée aux administrateurs.")
        st.stop()
    st.title("Administration")
    st.caption(
        "Gestion des comptes classiques. Par respect de la vie privée, tu vois des nombres "
        "(recherches, favoris), jamais leur contenu. Les administrateurs sont les membres de "
        "l'équipe, nommés avec `scripts/admin.py` dans le terminal du pod."
    )

    temp = st.session_state.pop(TEMP_KEY, None)
    if temp:
        st.success(
            f"Mot de passe provisoire de **{temp['username']}** (affiché une seule fois, "
            "transmets-le par un moyen privé ; il devra le changer à la connexion) :"
        )
        st.code(temp["password"], language=None)

    users = admin.list_users(con)
    if users.empty:
        st.info("Aucun compte.")
        return
    table = users.assign(
        role=users["is_admin"].map({True: "Administrateur", False: "Classique"}),
        etat=[
            "Bloqué" if b else ("Mot de passe provisoire" if m else "")
            for b, m in zip(users["bloque"], users["must_change_password"], strict=True)
        ],
        cree=users["created_at"].str[:10],
    )[["username", "role", "cree", "etat", "n_recherches", "n_favoris", "a_profil"]]
    c1, c2, c3 = st.columns(3)
    c1.metric("Comptes", len(users))
    c2.metric("Administrateurs", int(users["is_admin"].sum()), help=f"{admin.MAX_ADMINS} au plus")
    c3.metric("Bloqués", int(users["bloque"].sum()))
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "username": "Identifiant",
            "role": "Rôle",
            "cree": "Créé le",
            "etat": "État",
            "n_recherches": st.column_config.NumberColumn("Recherches"),
            "n_favoris": st.column_config.NumberColumn("Favoris"),
            "a_profil": st.column_config.CheckboxColumn("Profil"),
        },
    )

    st.subheader("Agir sur un compte")
    names = users["username"].tolist()
    target_name = st.selectbox("Compte", names, index=None, placeholder="Choisis un compte…")
    if target_name:
        t = users[users["username"] == target_name].iloc[0]
        tid = int(t["id"])
        is_self = tid == int(user["id"])
        a, b, c = st.columns(3)
        if a.button(
            "Débloquer",
            icon=":material/lock_open:",
            disabled=not t["bloque"],
            width="stretch",
            help="Annule le blocage après 5 échecs de connexion.",
        ):
            _run(lambda: admin.unlock(con, user["id"], tid), f"{target_name} débloqué.")
        if b.button(
            "Mot de passe provisoire",
            icon=":material/password:",
            disabled=bool(t["is_admin"]),
            width="stretch",
            help="Pour un utilisateur qui a oublié son mot de passe. Pas pour un administrateur.",
        ):
            try:
                pwd = admin.reset_password(con, user["id"], tid)
                st.session_state[TEMP_KEY] = {"username": target_name, "password": pwd}
                st.rerun()
            except accounts.AccountError as e:
                st.error(str(e))
        with c.popover(
            "Supprimer", icon=":material/delete:", disabled=bool(t["is_admin"]) or is_self
        ):
            st.write(f"Supprimer définitivement **{target_name}** (profil, historique, favoris) ?")
            if st.button("Oui, supprimer", type="primary", key=f"suppr_{tid}"):
                _run(lambda: admin.delete_account(con, user["id"], tid), f"{target_name} supprimé.")
        if t["is_admin"]:
            st.caption(
                "Compte administrateur : seul le déblocage est possible ici ; le reste se règle "
                "entre membres de l'équipe avec `scripts/admin.py`."
            )

    st.subheader("Journal des actions")
    log = admin.list_log(con)
    if log.empty:
        st.caption("Aucune action pour l'instant.")
    else:
        st.dataframe(
            log.rename(
                columns={
                    "created_at": "Date (UTC)",
                    "admin": "Par",
                    "action": "Action",
                    "cible": "Compte",
                    "details": "Détails",
                }
            ),
            hide_index=True,
            width="stretch",
        )


def _run(action, message: str) -> None:
    try:
        action()
        st.toast(message)
        st.rerun()
    except accounts.AccountError as e:
        st.error(str(e))
