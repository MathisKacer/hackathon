"""Fiche entreprise (T43) : en fenêtre par-dessus la page (Explorer, Entreprises) ou en panneau.

On choisit une entreprise de la couche orange et on voit tout ce qu'on sait d'elle :
identité, pourquoi elle est recommandée (explication T32 si disponible + décomposition du
score T42), besoin dans le domaine et niveau de preuve, offres récentes, situation BODACC (T23),
coordonnées et liens. Données : radar/fiche.py.

Coordination : le popup de la carte appartient à T32 (@mathis) ; ce panneau à T43 (@celia).

    open_fiche(siret, row)         # fenêtre ; row = ligne classée (score, distance) ou None
    render_fiche(spontaneous)      # ancien panneau avec sélecteur (gardé pour compatibilité)
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from commun import CHANCE_HELP, get_place
from favoris import star_button

from radar import fiche
from radar.domains import load_domains
from radar.paliers import rule_text, tier_text
from radar.spontaneous import COMPONENTS

MAX_CHOICES = 5000  # entreprises proposées (le sélecteur permet de taper pour chercher)
SITUATION_LABELS = {
    "sauvegarde": "🟡 Sauvegarde",
    "plan": "🟡 Plan",
    "redressement": "🟠 Redressement",
    "liquidation": "🔴 Liquidation",
    "fin": "✅ Fin de procédure",
    "autre": "· Autre annonce",
}


@st.cache_data(show_spinner=False)
def _company(siret: str) -> pd.Series | None:
    return fiche.load_company(siret)


@st.cache_data(show_spinner=False)
def _offers(siren: str | None, siret: str | None) -> pd.DataFrame:
    return fiche.company_offers(siren, siret)


@st.cache_data(show_spinner=False)
def _sites(siren: str, lat: float | None, lon: float | None) -> pd.DataFrame:
    return fiche.company_sites(siren, lat, lon)


@st.cache_data(show_spinner=False)
def _history(siren: str | None) -> pd.DataFrame:
    return fiche.bodacc_history(siren)


def _label(rank: int, r: pd.Series) -> str:
    name = str(r.get("nom") or "Entreprise")
    etab = r.get("nom_etablissement")
    if isinstance(etab, str) and etab and etab != name:
        name = f"{etab} ({name})"
    flag = str(r.get("alerte") or "")[:1]
    prio = tier_text(r.get("palier"), with_dots=False) or f"score {r['score']:.2f}"  # T65
    return f"{rank}. {name} — {r.get('commune') or ''} · {prio} {flag}".strip()


def _value(*vals) -> str | None:
    for v in vals:
        if v is not None and not (isinstance(v, float) and pd.isna(v)) and str(v).strip():
            return str(v)
    return None


def _identity(r: pd.Series, c: pd.Series) -> None:
    name = _value(c.get("nom"), r.get("nom")) or "Entreprise"
    etab = _value(c.get("nom_etablissement"), r.get("nom_etablissement"))
    st.markdown(f"### {name}" + (f" · {etab}" if etab and etab != name else ""))
    bits = [
        _value(c.get("naf_libelle"), r.get("naf_libelle")),
        _value(c.get("tranche_libelle"), r.get("tranche_effectif")),
        {
            "PME": "PME",
            "ETI": "ETI (entreprise de taille intermédiaire)",
            "GE": "Grande entreprise",
        }.get(str(c.get("categorie")), None),
        ("Siège" if c.get("siege") is True else "Établissement secondaire")
        if c.get("siege") is not None and pd.notna(c.get("siege"))
        else None,
    ]
    st.caption(" · ".join(b for b in bits if b))
    alerte = _value(r.get("alerte"))
    if alerte:
        coef = r.get("coef_procedure")
        reduit = (
            f" Score réduit (×{float(coef):.2f})."
            if coef is not None and pd.notna(coef) and float(coef) < 1
            else ""
        )
        (st.error if alerte.startswith("🔴") else st.warning)(
            f"{alerte}.{reduit} Détail dans « Situation »."
        )


def _star(siret: str, r: pd.Series, c: pd.Series) -> None:
    """Favori (T54) : étoile pour garder l'entreprise (retrouvée dans Mon espace)."""
    name = _value(c.get("nom"), r.get("nom")) or "Entreprise"
    etab = _value(c.get("nom_etablissement"), r.get("nom_etablissement"))
    label = f"{etab} ({name})" if etab and etab != name else name
    details = {
        "commune": _value(c.get("commune"), r.get("commune")),
        "siren": _value(c.get("siren"), r.get("siren")),
        "secteur": _value(c.get("naf_libelle"), r.get("naf_libelle")),
        "taille": _value(c.get("tranche_libelle")),
    }
    star_button("entreprise", str(siret), label, details, key=f"fav_fiche_{siret}")


def _why(r: pd.Series) -> None:
    if r.get("score") is None or pd.isna(r.get("score")):
        return  # entreprise ouverte depuis la recherche : pas de score final (ni distance)
    st.markdown("#### Pourquoi elle est recommandée")
    explication = _value(r.get("explication"))  # T32 (@mathis), si disponible
    if explication:
        st.info(explication)
    c1, c2, c3 = st.columns(3)
    # T65 (D32) : palier en mots ; le score reste visible juste en dessous.
    prio = tier_text(r.get("palier")) if pd.notna(r.get("palier", None)) else ""
    c1.metric(
        "Priorité" if prio else "Score",
        prio or f"{r['score']:.2f}",
        delta=f"score {r['score']:.2f}" if prio else None,
        delta_color="off",
        delta_arrow="off",
        help=(rule_text() + " Score = moyenne pondérée des critères (0 à 1).")
        if prio
        else "Moyenne pondérée des composantes (0 à 1).",
    )
    if pd.notna(r.get("distance_km")):
        c2.metric("Distance", f"{r['distance_km']:.1f} km")
    p = r.get("p_reponse")
    if p is not None and pd.notna(p):
        c3.metric("Chance de réponse", f"{100 * float(p):.0f} %", help=CHANCE_HELP)
    apports = [
        (label, float(r[f"apport_{k}"]), float(r[k]) if pd.notna(r.get(k)) else None, help_)
        for k, (label, help_) in COMPONENTS.items()
        if pd.notna(r.get(f"apport_{k}")) and float(r[f"apport_{k}"]) > 0
    ]
    if apports:
        st.caption("Décomposition du score : apport de chaque composante (la somme = le score).")
        for label, apport, value, help_ in apports:
            a, b = st.columns([2, 3])
            a.markdown(f"**{label}**", help=help_)
            b.progress(
                min(apport / max(r["score"], 1e-9), 1.0),
                text=f"+{apport:.2f}" + (f" (valeur {value:.2f})" if value is not None else ""),
            )


def _hiring(r: pd.Series, domaine: str | None) -> None:
    """T38 (D27) : La Bonne Boîte signale-t-elle l'établissement, ou est-ce une estimation ?"""
    sig = fiche.hiring_signal(r)
    if sig is None:
        return
    label = load_domains()[domaine].label.lower() if domaine in load_domains() else "ce domaine"
    if sig["lbb"]:
        pot = sig["potentiel"]
        detail = (
            f" Potentiel d'embauche : **{pot:.1f}** (médiane des établissements signalés : "
            f"{fiche.LBB_MEDIAN_POTENTIEL:.1f})."
            if pot is not None
            else ""
        )
        st.success(
            f"✔ Signalée par **La Bonne Boîte** (France Travail) comme susceptible d'embaucher "
            f"en {label}.{detail}"
        )
    else:
        st.caption(
            "Potentiel d'embauche estimé d'après les offres du secteur et la taille de "
            "l'établissement : La Bonne Boîte ne le signale pas."
        )


def _need(r: pd.Series, domaine: str | None = None) -> None:
    st.markdown("#### Besoin dans le domaine")
    e = fiche.evidence(r)
    icon = {"élevé": "🟢", "moyen": "🟡", "faible": "⚪", "non collecté": "⚪"}[e["niveau"]]
    st.markdown(f"Niveau de preuve : {icon} **{e['niveau']}** — {e['explication_niveau']}.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Offres du domaine", e["n_offres"], help="Toute l'entreprise (SIREN), tous contrats.")
    c2.metric("dont stages", e["n_stage"])
    c3.metric("dont alternances", e["n_alternance"])
    if e["intensite"] is not None:
        txt = f"Intensité estimée : **{e['intensite']:.2f} offre(s) du domaine pour 100 salariés**"
        if e["ic_bas"] is not None and e["ic_haut"] is not None:
            txt += f" (intervalle crédible à 90 % : {e['ic_bas']:.2f} – {e['ic_haut']:.2f})"
        if e["moyenne_secteur"] is not None:
            txt += f" ; moyenne du secteur : {e['moyenne_secteur']:.2f}"
        st.markdown(txt + ".")
    _hiring(r, domaine)


def _offers_block(siren: str | None, siret: str | None) -> None:
    st.markdown("#### Offres récentes de l'entreprise")
    offers = _offers(siren, siret)
    if offers.empty:
        st.caption("Aucune offre rapprochée de cette entreprise dans les données collectées.")
        return
    st.dataframe(
        offers.rename(
            columns={
                "date_publication": "Publiée le",
                "titre": "Offre",
                "contrat": "Contrat",
                "domaine": "Domaine",
                "commune": "Lieu",
                "source": "Source",
                "url": "Annonce",
            }
        ),
        hide_index=True,
        width="stretch",
        column_config={"Annonce": st.column_config.LinkColumn("Annonce", display_text="Voir")},
    )


def _situation(siren: str | None) -> None:
    history = _history(siren)
    with st.expander(f"Situation (BODACC) — {len(history)} annonce(s) sur 2 ans"):
        if history.empty:
            st.caption("Aucune procédure collective publiée au BODACC ces 2 dernières années.")
            return
        st.dataframe(
            history.assign(situation=history["situation"].map(SITUATION_LABELS)).rename(
                columns={
                    "date": "Date",
                    "situation": "Situation",
                    "nature": "Jugement",
                    "url": "Annonce",
                }
            ),
            hide_index=True,
            width="stretch",
            column_config={
                "Date": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Annonce": st.column_config.LinkColumn("Annonce", display_text="BODACC"),
            },
        )


def _contact(r: pd.Series, c: pd.Series) -> None:
    st.markdown("#### Coordonnées et liens")
    adresse = _value(c.get("adresse"))
    if c.get("diffusion_partielle") is True:
        adresse = None  # l'établissement a demandé à ne pas diffuser son adresse
    lieu = " ".join(x for x in (_value(c.get("code_postal")), _value(c.get("commune"))) if x)
    st.markdown(
        "  \n".join(
            x
            for x in (
                f"📍 {adresse}, {lieu}" if adresse else (f"📍 {lieu}" if lieu else None),
                f"SIRET {r['siret']} · SIREN {_value(c.get('siren'), r.get('siren')) or '—'}",
            )
            if x
        )
    )
    row = pd.concat([c, r]) if not c.empty else r
    row = row[~row.index.duplicated(keep="last")]
    st.markdown(" · ".join(f"[{name}]({url})" for name, url in fiche.links(row).items()))


def fiche_content(siret: str, row: pd.Series | None = None, domaine: str | None = None) -> None:
    """Contenu complet de la fiche d'un établissement.

    `row` : ligne de la liste des candidatures spontanées (score, distance, alerte…) ; sans
    elle (recherche d'entreprises), on lit les indicateurs du domaine dans scores.parquet.
    """
    c = _company(siret)
    c = c if c is not None else pd.Series(dtype=object)
    if row is None:
        s = fiche.load_scores(siret, domaine) if domaine else None
        parts = [x for x in (c, s) if x is not None and not x.empty]
        row = pd.concat(parts) if parts else pd.Series({"siret": siret})
        row = row[~row.index.duplicated(keep="last")]
        if "alerte" not in row and "procedure_type" in row:
            from radar.procedures import alert_text

            row["alerte"] = alert_text(row.get("procedure_type"), row.get("procedure_date"))
    siren = _value(c.get("siren"), row.get("siren"))
    _identity(row, c)
    if NAV_KEY in st.session_state and siren:
        _parent_company(siren)
    _star(siret, row, c)
    _why(row)
    _need(row, domaine)
    _offers_block(siren, siret)
    _situation(siren)
    _contact(row, c)


# --- Entreprise (SIREN) et site (SIRET) dans la même fenêtre (T57) -----------------------

NAV_KEY = "_fiche_nav"  # {"origin": (type, id), "view": (type, id)} ; type = "site" | "entreprise"


def _go(view: tuple[str, str]) -> None:
    st.session_state[NAV_KEY]["view"] = view


def _parent_company(siren: str) -> None:
    """Dans la fiche d'un site : « Fait partie de X · N sites » + « Voir toute l'entreprise »."""
    sites = _sites(siren, None, None)
    if len(sites) <= 1:
        return
    summary = fiche.company_summary(sites, siren)
    left, right = st.columns([3, 1], vertical_alignment="center")
    left.markdown(f"Fait partie de **{summary['nom']}** · {summary['n_sites']} sites en France")
    right.button(
        "Voir toute l'entreprise",
        key=f"vers_entreprise_{siren}",
        on_click=_go,
        args=(("entreprise", siren),),
        width="stretch",
    )


def company_content(siren: str, domaine: str | None = None) -> None:
    """Fiche d'une entreprise entière : identité, offres de tous les sites, sites, BODACC."""
    place = get_place(st.session_state.get("ville"))
    sites = _sites(siren, place.lat if place else None, place.lon if place else None)
    if sites.empty:
        st.write("Entreprise introuvable dans le référentiel (sites d'au moins 10 salariés).")
        return
    s = fiche.company_summary(sites, siren)
    st.markdown(f"### {s['nom']}")
    eff = (
        f"environ {s['effectif_total']:,} salariés".replace(",", " ")
        if s["effectif_total"]
        else None
    )
    cat = {
        "PME": "PME",
        "ETI": "ETI (entreprise de taille intermédiaire)",
        "GE": "Grande entreprise",
    }
    bits = [
        cat.get(s["categorie"]),
        s["activite"],
        f"{s['n_sites']} site{'s' if s['n_sites'] > 1 else ''} en France",
        eff,
        f"siège à {s['siege_commune'].title()}" if s["siege_commune"] else None,
    ]
    st.caption(" · ".join(b for b in bits if b))
    if s["procedure_type"]:
        from radar.procedures import alert_text

        txt = alert_text(s["procedure_type"], s["procedure_date"])
        (st.error if txt.startswith("🔴") else st.warning)(f"{txt}. Détail dans « Situation ».")
    star_button(
        "entreprise",
        f"siren:{siren}",
        f"{s['nom']} (toute l'entreprise)",
        {
            "commune": s["siege_commune"],
            "siren": siren,
            "secteur": s["activite"],
            "taille": f"{s['n_sites']} sites",
        },
        key=f"fav_entreprise_{siren}",
    )

    st.markdown("#### Offres de l'entreprise (tous ses sites)")
    offers = _offers(siren, None)
    if offers.empty:
        st.caption("Aucune offre rapprochée de cette entreprise dans les données collectées.")
    else:
        st.dataframe(
            offers.rename(
                columns={
                    "date_publication": "Publiée le",
                    "titre": "Offre",
                    "contrat": "Contrat",
                    "domaine": "Domaine",
                    "commune": "Lieu",
                    "source": "Source",
                    "url": "Annonce",
                }
            ),
            hide_index=True,
            width="stretch",
            column_config={"Annonce": st.column_config.LinkColumn("Annonce", display_text="Voir")},
        )

    st.markdown(f"#### Ses sites ({len(sites)})")
    table = pd.DataFrame(
        {
            "Site": sites["nom_etablissement"]
            .fillna("")
            .where(sites["nom_etablissement"].fillna("") != sites["nom"].fillna(""), ""),
            "Lieu": sites["commune"].fillna("") + " " + sites["code_postal"].fillna("").astype(str),
            "Taille": sites["tranche_libelle"],
            "Siège": sites["siege"].fillna(False).astype(bool).map({True: "Siège", False: ""}),
        }
    )
    if place is not None:
        table["Distance"] = sites["distance_km"]
    event = st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="single-row",
        key=f"sites_{siren}",
        column_config={"Distance": st.column_config.NumberColumn(format="%.1f km")},
    )
    st.caption(
        ("Les plus proches de ta ville d'abord. " if place is not None else "")
        + "Sites d'au moins 10 salariés. Clique sur un site pour ouvrir sa fiche."
    )
    rows = event.selection.rows if event is not None else []
    if rows:
        _go(("site", str(sites.iloc[rows[0]]["siret"])))
        st.rerun(scope="fragment")
    _situation(siren)
    st.markdown(f"[Annuaire des entreprises]({s['url_annuaire']})")


def _close_fiche() -> None:
    # Fenêtre fermée : on vide la sélection de la liste pour pouvoir rouvrir la même fiche.
    st.session_state["_liste_version"] = st.session_state.get("_liste_version", 0) + 1
    st.session_state.pop(NAV_KEY, None)


@st.dialog("Fiche", width="large", on_dismiss=_close_fiche)
def open_fiche(
    siret: str | None,
    row: pd.Series | None = None,
    domaine: str | None = None,
    siren: str | None = None,
) -> None:
    """Fenêtre de fiche : un site (`siret`) ou une entreprise entière (`siren`, T57).

    On passe de l'un à l'autre dans la même fenêtre (« Voir toute l'entreprise », clic sur un
    site, « ← Retour »).
    """
    origin = ("site", str(siret)) if siret else ("entreprise", str(siren))
    nav = st.session_state.get(NAV_KEY)
    if not nav or nav["origin"] != origin:
        nav = {"origin": origin, "view": origin}
        st.session_state[NAV_KEY] = nav
    kind, ident = nav["view"]
    if nav["view"] != nav["origin"]:
        if kind == "entreprise":  # venu d'un site
            st.button("← Retour au site", key="fiche_retour", on_click=_go, args=(nav["origin"],))
        else:  # un site ouvert depuis la liste de l'entreprise (SIREN = 9 premiers chiffres)
            st.button(
                "← Toute l'entreprise",
                key="fiche_retour",
                on_click=_go,
                args=(("entreprise", ident[:9]),),
            )
    if kind == "entreprise":
        company_content(ident, domaine)
    else:
        fiche_content(ident, row if ident == str(siret) else None, domaine)


def render_fiche(spontaneous: pd.DataFrame) -> None:
    """Affiche le sélecteur et la fiche de l'entreprise choisie (rien si la liste est vide)."""
    if spontaneous is None or spontaneous.empty:
        return
    st.subheader("🔎 Fiche entreprise")
    top = spontaneous.head(MAX_CHOICES).reset_index(drop=True)
    labels = {r["siret"]: _label(i + 1, r) for i, r in top.iterrows()}
    siret = st.selectbox(
        "Choisis une entreprise de la liste 🟠 (tape un nom pour chercher)",
        list(labels),
        format_func=labels.get,
        key="fiche_siret",
        help="Dans l'ordre du classement ; tape le début d'un nom pour la retrouver.",
    )
    if siret is None:
        return
    r = top[top["siret"] == siret].iloc[0]
    with st.container(border=True):
        fiche_content(siret, r)
