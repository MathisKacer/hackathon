"""Dépôt du CV et liste « Tes compétences » (T45, T83), partagés par Explorer et Mon espace.

La liste est le widget de clé `competences` (réglage de `app/commun.py`, gardé dans le profil,
D41). On peut y choisir des compétences de la liste ou en **taper de nouvelles** (« QGIS »).
Le PDF reste en mémoire le temps de la lecture : rien n'est écrit sur le disque.
"""

from __future__ import annotations

import streamlit as st

from radar.competences import SKILL_LABELS, clean_skills, detect_skills, pdf_text

KEY = "competences"
MESSAGE_KEY = "_cv_message"


def _read_cv(file_key: str) -> None:
    """Rappel du dépôt : compétences lues dans le CV, ajoutées à la liste."""
    fichier = st.session_state.get(file_key)
    if fichier is None:
        return
    found = detect_skills(pdf_text(fichier.getvalue()))
    st.session_state[KEY] = clean_skills(list(st.session_state.get(KEY, [])) + found)
    s = "s" if len(found) > 1 else ""
    st.session_state[MESSAGE_KEY] = (
        f"{len(found)} compétence{s} trouvée{s} dans ton CV. Tu peux corriger la liste."
        if found
        else "Aucune compétence reconnue : le PDF est peut-être une image scannée. "
        "Choisis ou tape tes compétences dans la liste."
    )


def _clean() -> None:
    st.session_state[KEY] = clean_skills(st.session_state.get(KEY, []))


def cv_and_skills(file_key: str) -> list[str]:
    """Dépôt du CV + liste des compétences (modifiable, saisie libre) ; renvoie la liste."""
    st.file_uploader(
        "Dépose ton CV (PDF)",
        type="pdf",
        key=file_key,
        on_change=_read_cv,
        args=(file_key,),
        help="On y repère tes compétences (Python, SQL, comptabilité…) pour afficher ta "
        "correspondance avec chaque entreprise (sans changer le score). "
        "Ton CV n'est pas conservé.",
    )
    if msg := st.session_state.pop(MESSAGE_KEY, None):
        st.caption(msg)
    # Nettoyée avant le widget, quelle que soit son origine (profil, CV, saisie, ancien état)
    current = clean_skills(st.session_state.get(KEY, []))
    if KEY in st.session_state and st.session_state[KEY] != current:
        st.session_state[KEY] = current
    extra = [s for s in current if s not in SKILL_LABELS]
    return st.multiselect(
        "Tes compétences",
        SKILL_LABELS + extra,
        key=KEY,
        accept_new_options=True,
        on_change=_clean,
        placeholder="Choisis, tape une compétence ou dépose ton CV",
        help="Tu peux taper une compétence qui n'est pas dans la liste (ex. QGIS), puis Entrée. "
        "Seules celles que Radar sait reconnaître dans les offres comptent dans la "
        "correspondance ; les autres sont gardées dans ton profil.",
    )
