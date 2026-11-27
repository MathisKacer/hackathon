"""Page « Mon espace » : connexion facultative, profil, favoris et historique (T48, T49, T54)."""

from __future__ import annotations

import streamlit as st
from commun import PAGES_DIR, PROFILE_LABELS, all_regions_of, get_offers, profile_keys
from compte import _con, account_page, current_user
from favoris import favorites, remove
from fiche_ui import open_fiche

from radar import accounts


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
    st.subheader("Mes favoris")
    if not companies and not offers_fav:
        st.write(
            "Ajoute des entreprises (☆ dans leur fiche) ou des offres (case ★ dans la liste) "
            "pour les retrouver ici."
        )
        return
    if not connected:
        st.caption("Favoris temporaires : crée un compte ou connecte-toi pour les garder.")
    tab_c, tab_o = st.tabs([f"Entreprises ({len(companies)})", f"Offres ({len(offers_fav)})"])
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
                if b1.button("Voir la fiche", key=f"fav_voir_{f['ref']}", width="stretch"):
                    to_open = f["ref"]
                b2.button(
                    "Retirer",
                    key=f"fav_retirer_e_{f['ref']}",
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
                    b1.link_button("Voir l'offre", d["url"], width="stretch")
                b2.button(
                    "Retirer",
                    key=f"fav_retirer_o_{f['ref']}",
                    on_click=remove,
                    args=("offre", f["ref"]),
                    width="stretch",
                )
                _follow_up(f, connected)
    if to_open:
        open_fiche(to_open, None, st.session_state.get("domaine"))


account_page(
    profile_keys(all_regions_of(get_offers())),
    PROFILE_LABELS,
    PAGES_DIR / "explorer.py",
    favorites_section,
)
