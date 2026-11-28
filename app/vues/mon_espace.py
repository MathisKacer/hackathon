"""Page « Mon espace » : connexion facultative, profil, favoris et historique (T48, T49, T54)."""

from __future__ import annotations

from datetime import datetime

import streamlit as st
from commun import PAGES_DIR, PROFILE_LABELS, get_offers, profile_keys, saved_profile_keys
from compte import TZ, _con, account_page, current_user
from cv_ui import profile_skills_editor
from favoris import favorites, remove
from fiche_ui import open_fiche
from recherches import saved_section
from style import GREEN, RED, pill

from radar import accounts
from radar.export import candidatures_csv

STATUT_COLORS = {
    "Envoyée": "#1a56db",
    "Relancée": "#e8590c",
    "Entretien": "#6d28d9",
    "Réponse positive": GREEN,
    "Réponse négative": RED,
    "Sans réponse": "#6B7280",
}


def _save_note(kind: str, ref: str, key: str) -> None:
    user = current_user()
    if user is not None:
        try:
            accounts.update_favorite(_con(), user["id"], kind, ref, note=st.session_state[key])
        except accounts.AccountError as e:
            st.toast(str(e))


def _save_candidate(kind: str, ref: str, key: str) -> None:
    user = current_user()
    if user is not None:
        accounts.update_favorite(_con(), user["id"], kind, ref, candidate=st.session_state[key])


def _save_statut(kind: str, ref: str, key: str) -> None:
    user = current_user()
    if user is not None:
        accounts.update_favorite(_con(), user["id"], kind, ref, statut=st.session_state[key])


def _follow_up(f: dict, connected: bool) -> None:
    """Case « Candidaté » et note libre (seulement avec un compte)."""
    if not connected:
        return
    kind, ref = f["kind"], f["ref"]
    c1, c2 = st.columns([1, 3], vertical_alignment="center")
    k_cand, k_note = f"fav_cand_{kind}_{ref}", f"fav_note_{kind}_{ref}"
    st.session_state.setdefault(k_cand, f["candidate"])
    st.session_state.setdefault(k_note, f["note"])
    c1.checkbox("Candidaté", key=k_cand, on_change=_save_candidate, args=(kind, ref, k_cand))
    c2.text_input(
        "Note",
        key=k_note,
        on_change=_save_note,
        args=(kind, ref, k_note),
        placeholder="Une note pour toi (contact, date de relance…)",
        label_visibility="collapsed",
    )


def favorites_section() -> None:
    connected = current_user() is not None
    companies, offers_fav = favorites("entreprise"), favorites("offre")
    if not connected:
        st.subheader("Mes favoris")
    if not companies and not offers_fav:
        st.write(
            "Ajoute des entreprises (☆ dans leur fiche) ou des offres (case ★ dans la liste) "
            "pour les retrouver ici."
        )
        return
    if not connected:
        st.caption("Favoris temporaires : crée un compte ou connecte-toi pour les garder.")
    # Libellés sans compteurs : sinon « Retirer » ramènerait au premier onglet
    tab_c, tab_o = st.tabs(["Entreprises", "Offres"])
    to_open = None
    with tab_c:
        for f in companies:
            d = f["details"]
            with st.container(border=True):
                left, b1, b2 = st.columns([4, 1, 1], vertical_alignment="center")
                left.markdown(f"**{f['label']}**")
                left.caption(
                    " · ".join(
                        x for x in (d.get("commune"), d.get("secteur"), d.get("taille")) if x
                    )
                )
                if b1.button(
                    "Voir la fiche",
                    key=f"fav_voir_{f['ref']}",
                    width="stretch",
                    icon=":material/open_in_new:",
                ):
                    to_open = f["ref"]
                b2.button(
                    "Retirer",
                    type="tertiary",
                    key=f"fav_retirer_e_{f['ref']}",
                    icon=":material/delete:",
                    on_click=remove,
                    args=("entreprise", f["ref"]),
                    width="stretch",
                )
                _follow_up(f, connected)
    with tab_o:
        o = get_offers()
        online = set(o["source"].astype(str) + ":" + o["offre_id"].astype(str))
        for f in offers_fav:
            d = f["details"]
            with st.container(border=True):
                left, b1, b2 = st.columns([4, 1, 1], vertical_alignment="center")
                left.markdown(f"**{f['label']}**")
                bits = [d.get("commune"), (d.get("contrat") or "").capitalize() or None]
                if f["ref"] not in online:
                    bits.append("n'est plus en ligne")
                left.caption(" · ".join(x for x in bits if x))
                if d.get("url"):
                    b1.link_button(
                        "Voir l'offre", d["url"], width="stretch", icon=":material/link:"
                    )
                b2.button(
                    "Retirer",
                    type="tertiary",
                    key=f"fav_retirer_o_{f['ref']}",
                    icon=":material/delete:",
                    on_click=remove,
                    args=("offre", f["ref"]),
                    width="stretch",
                )
                _follow_up(f, connected)
    if to_open:
        domaine = st.session_state.get("domaine")
        if to_open.startswith("siren:"):  # favori « toute l'entreprise » (T57)
            open_fiche(None, None, domaine, siren=to_open.removeprefix("siren:"))
        else:
            open_fiche(to_open, None, domaine)


def _mark_followed_up(kind: str, ref: str, key: str) -> None:
    st.session_state[key] = "Relancée"
    _save_statut(kind, ref, key)


def _dates(f: dict) -> str:
    """« envoyée le 12/11 · relancée le 27/11 » (T90)."""
    sent = f["envoyee_le"].astimezone(TZ).strftime("%d/%m")
    label = "ajoutée aux favoris le" if f["date_estimee"] else "envoyée le"
    text = f"{label} {sent}"
    if f["relancee_le"]:
        text += f" · relancée le {f['relancee_le'].astimezone(TZ).strftime('%d/%m')}"
    return text


def candidatures_section() -> None:
    """Favoris cochés « Candidaté » (T82), avec leur statut en couleur."""
    applied = [f for f in favorites() if f["candidate"]]
    if not applied:
        st.write("Coche « Candidaté » sur un favori pour le retrouver ici et suivre sa réponse.")
        return
    due = {(f["kind"], f["ref"]) for f in applied if accounts.a_relancer(f)}
    if due:
        s = "s" if len(due) > 1 else ""
        st.warning(
            f"{len(due)} candidature{s} à relancer : "
            f"{accounts.RELANCE_DELAY.days} jours ou plus sans réponse.",
            icon=":material/schedule_send:",
        )
    applied.sort(key=lambda f: (f["kind"], f["ref"]) not in due)  # à relancer en premier
    st.download_button(  # T91
        "Télécharger mes candidatures",
        data=candidatures_csv(applied),
        file_name=f"candidatures_{datetime.now(TZ):%Y-%m-%d}.csv",
        mime="text/csv",
        icon=":material/download:",
        help="Tableau à ouvrir dans Excel, LibreOffice ou Google Sheets.",
    )
    for f in applied:
        kind_ref = f"{f['kind']}_{f['ref']}"
        key = f"fav_statut_{kind_ref}"
        st.session_state.setdefault(key, f["statut"] or accounts.CANDIDATURE_STATUTS[0])
        with st.container(border=True, key=f"espace_candidature_{kind_ref.replace(':', '_')}"):
            left, middle, right = st.columns([3, 1.3, 1.5], vertical_alignment="center")
            left.markdown(f"**{f['label']}**")
            kind = "Entreprise" if f["kind"] == "entreprise" else "Offre"
            left.caption(" · ".join(x for x in (kind, _dates(f), f["note"]) if x))
            statut = st.session_state[key]
            pills = pill(statut, STATUT_COLORS.get(statut, "#6B7280"))
            if (f["kind"], f["ref"]) in due:
                pills += " " + pill("À relancer", "#c2410c")
            middle.markdown(pills, unsafe_allow_html=True)
            right.selectbox(
                "Statut",
                accounts.CANDIDATURE_STATUTS,
                key=key,
                on_change=_save_statut,
                args=(f["kind"], f["ref"], key),
                label_visibility="collapsed",
            )
            if (f["kind"], f["ref"]) in due:
                # Bouton nécessaire pour une 2e relance : le statut est déjà « Relancée »
                right.button(
                    "J'ai relancé",
                    key=f"fav_relance_{kind_ref}",
                    icon=":material/send:",
                    on_click=_mark_followed_up,
                    args=(f["kind"], f["ref"], key),
                    width="stretch",
                )


account_page(
    profile_keys(),
    PROFILE_LABELS,
    PAGES_DIR / "explorer.py",
    favorites_section,
    saved_keys=saved_profile_keys(),  # T81 : le profil ne garde que les compétences du CV
    # T83, T86 : compétences une à une (✕ pour retirer, ajout et CV enregistrés aussitôt)
    profile_editor=profile_skills_editor,
    candidatures_section=candidatures_section,
    searches_section=saved_section,  # T84 : recherches enregistrées
)
