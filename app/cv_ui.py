"""Dépôt du CV et compétences (T45, T83, T86) : liste d'Explorer, éditeur du profil (Mon espace).

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


# --- T86 : Mon espace › Mes compétences, une à une, enregistrées aussitôt ----------------------

ADD_KEY = "competence_ajout"


def _sync_search(add: list[str] = (), remove: str | None = None) -> None:
    """Répercute l'ajout / le retrait sur la recherche en cours (liste d'Explorer)."""
    now = [s for s in st.session_state.get(KEY, []) if s != remove]
    st.session_state[KEY] = clean_skills(now + list(add))


def _remove_skill(skill: str, saved: list[str], save) -> None:
    save({KEY: [s for s in saved if s != skill]})
    _sync_search(remove=skill)
    st.toast(f"« {skill} » retirée de ton profil.")


def _add_skill(saved: list[str], save) -> None:
    value = st.session_state.get(ADD_KEY)
    st.session_state[ADD_KEY] = None  # le champ se vide après l'ajout
    new = clean_skills(saved + [value])
    if new != saved:
        save({KEY: new})
        _sync_search(add=new[len(saved) :])
        st.toast(f"« {new[-1]} » ajoutée à ton profil.")


def _add_cv(file_key: str, saved: list[str], save) -> None:
    fichier = st.session_state.get(file_key)
    if fichier is None:
        return
    found = detect_skills(pdf_text(fichier.getvalue()))
    new = clean_skills(saved + found)
    if new != saved:
        save({KEY: new})
        _sync_search(add=found)
    added = len(new) - len(saved)
    s = "s" if added > 1 else ""
    st.session_state[MESSAGE_KEY] = (
        f"{added} compétence{s} ajoutée{s} depuis ton CV (enregistrée{s})."
        if added
        else "Aucune nouvelle compétence reconnue dans ce CV (déjà là, ou PDF scanné)."
    )


def profile_skills_editor(profile: dict, save, file_key: str = "cv_fichier_profil") -> None:
    """Compétences du profil : une étiquette ✕ par compétence (retirée aussitôt), un champ pour
    en ajouter une (liste ou texte libre, enregistrée aussitôt) et le dépôt du CV."""
    saved = clean_skills(profile.get(KEY))
    if saved:
        with st.container(horizontal=True, gap="small"):
            for i, skill in enumerate(saved):
                st.button(
                    skill,
                    key=f"competence_suppr_{i}",
                    icon=":material/close:",
                    on_click=_remove_skill,
                    args=(skill, saved, save),
                    help=f"Retirer « {skill} » de ton profil",
                )
    else:
        st.caption("Aucune compétence enregistrée : dépose ton CV ou ajoute-les une à une.")
    st.selectbox(
        "Ajouter une compétence",
        [s for s in SKILL_LABELS if s not in saved],
        index=None,
        key=ADD_KEY,
        accept_new_options=True,
        on_change=_add_skill,
        args=(saved, save),
        placeholder="Choisis ou tape une compétence (ex. QGIS), puis Entrée",
        help="Enregistrée tout de suite dans ton profil. Seules les compétences que Radar sait "
        "reconnaître dans les offres comptent dans la correspondance.",
    )
    st.file_uploader(
        "Ou dépose ton CV (PDF)",
        type="pdf",
        key=file_key,
        on_change=_add_cv,
        args=(file_key, saved, save),
        help="Ses compétences sont ajoutées à ton profil ; tu peux ensuite retirer celles "
        "qui ne te correspondent pas. Ton CV n'est pas conservé.",
    )
    if msg := st.session_state.pop(MESSAGE_KEY, None):
        st.caption(msg)
