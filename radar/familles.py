"""Familles de marque : relier les sociétés d'un même groupe par leur nom (T26, L7, L24, D36).

    fam = build_families(entreprises, scores)        # une ligne par SIREN d'ETI/GE en famille
    df = mark_family_offers(spontaneous, fam, contrat="Stage")

Aucune donnée ouverte ne dit qui appartient à quel groupe : une offre est rattachée à **une**
société (Thales Six GTS), et ses sœurs (Thales Simulation…) paraissent « sans offre ». On
regroupe donc les **ETI et grandes entreprises** par **clé de marque** = premier mot du nom
normalisé, ou les deux premiers quand le premier est générique (« crédit mutuel », « saint
gobain »). Une famille = au moins deux SIREN partageant la clé.

Décision D36 : les sociétés sœurs restent dans la couche orange, **signalées** (« le groupe
publie déjà N offres ») ; elles ne sont jamais masquées.
"""

from __future__ import annotations

import pandas as pd

from radar.process.match_siret import normalize

BIG_CATEGORIES = ("ETI", "GE")
MIN_KEY_LENGTH = 3
# Premiers mots trop courants pour désigner une marque : on prend alors les deux premiers mots
# (si le second n'est pas générique non plus). Revu sur les plus grosses familles obtenues.
GENERIC_WORDS = set(
    """
    societe soc ste caisse centre centres compagnie cie saint sainte st institut ca departement
    ecole fondation laboratoires laboratoire labo credit agence in universite euro air assistance
    editions maisons maison banque france groupe group cabinet clinique hopital association union
    mutuelle mutuelles federation office entreprise entreprises etablissements etablissement ets
    generale general generales nouvelle nouvelles international internationale services service
    transports transport commune ville syndicat regie conseil residence new bureau atelier ateliers
    comptoir distribution industrie industries immobiliere immobilier pharmacie garage hotel
    hotels restaurant agricole cooperative coop scop anonyme francaise francais national nationale
    regional regionale region regions electricite electrique pierre action actions centrale
    communaute communautaire metropole conseils assurances assurance mutualite clinique polyclinique
    gestion ehpad home domaine chateau club sport sports europe european europeenne ouest est nord
    sud atlantique bretagne normandie provence alsace lorraine aquitaine occitanie paris lyon
    marseille groupement gip gcs sem spl sdis cci cma chambre chambres caisses office offices
    habitat logement logements foyer foyers technique techniques systemes system systems solutions
    group global ministere pour business eden harmonie ligue casino como
    le la les des du de et a b c d e f g h i j k l m n o p q r s t u v w x y z
    """.split()
)


def brand_key(name: str | None) -> str | None:
    """Clé de marque d'un nom de société, ou None si on ne peut pas en tirer une marque."""
    words = [w for w in normalize(name).split() if len(w) >= 2]
    if not words:
        return None
    first = words[0]
    if first not in GENERIC_WORDS:
        return first if len(first) >= MIN_KEY_LENGTH else None
    if len(words) >= 2 and words[1] not in GENERIC_WORDS and len(words[1]) >= MIN_KEY_LENGTH:
        return f"{first} {words[1]}"
    return None


def build_families(
    entreprises: pd.DataFrame, scores: pd.DataFrame, domaine: str = "data"
) -> pd.DataFrame:
    """Une ligne par SIREN d'ETI/GE appartenant à une famille d'au moins deux sociétés.

    Colonnes : `siren, famille, famille_nom` (la marque, lisible : « Credit Mutuel »),
    `famille_n_societes`, et les offres **du domaine** de chaque société
    (`n_offres_domaine_siren`, `n_stage_domaine_siren`, `n_alternance_domaine_siren`) : les
    totaux de la famille se calculent selon le contrat visé (`mark_family_offers`).
    """
    cols = ["siren", "nom", "categorie"]
    ent = entreprises[[c for c in cols if c in entreprises]].drop_duplicates("siren")
    ent = ent[ent["categorie"].isin(BIG_CATEGORIES)].copy()
    ent["famille"] = ent["nom"].map(brand_key)
    ent = ent.dropna(subset=["famille"])
    size = ent.groupby("famille")["siren"].transform("size")
    ent = ent[size >= 2].assign(famille_n_societes=size[size >= 2])
    offer_cols = ["n_offres_domaine_siren", "n_stage_domaine_siren", "n_alternance_domaine_siren"]
    sc = scores
    if "domaine" in sc:
        sc = sc[sc["domaine"] == domaine]
    present = [c for c in offer_cols if c in sc]
    offers = sc.groupby("siren")[present].max() if present else pd.DataFrame()
    ent = ent.merge(offers, left_on="siren", right_index=True, how="left")
    for c in offer_cols:
        ent[c] = ent[c].fillna(0).astype(int) if c in ent else 0
    ent["famille_nom"] = ent["famille"].str.title()  # « Geodis », « Credit Mutuel »
    out_cols = ["siren", "famille", "famille_nom", "famille_n_societes", *offer_cols]
    return ent[out_cols].reset_index(drop=True)


def _matching(df: pd.DataFrame, contrat: str) -> pd.Series:
    """Offres du domaine correspondant au contrat visé (mêmes règles que spontaneous)."""
    total, stage, alt = (
        df["n_offres_domaine_siren"],
        df["n_stage_domaine_siren"],
        df["n_alternance_domaine_siren"],
    )
    return {"stage": stage, "alternance": alt, "emploi": total - stage - alt}.get(
        contrat.lower(), total
    )


def mark_family_offers(df: pd.DataFrame, families: pd.DataFrame, contrat: str) -> pd.DataFrame:
    """Ajoute `famille_nom`, `famille_offres` (offres du domaine pour ce contrat publiées par
    **les autres** sociétés de la famille) et `famille_societes_avec_offre`.

    `famille_offres` = 0 pour une société hors famille ou dont la famille ne publie rien.
    """
    out = df.copy()
    empty = {"famille_nom": None, "famille_offres": 0, "famille_societes_avec_offre": 0}
    if out.empty or families is None or families.empty or "siren" not in out:
        return out.assign(**empty)
    fam = families.assign(_m=_matching(families, contrat).clip(lower=0))
    totals = fam.groupby("famille").agg(
        _tot=("_m", "sum"), _n_with=("_m", lambda s: int((s > 0).sum()))
    )
    fam = fam.join(totals, on="famille")
    fam["famille_offres"] = (fam["_tot"] - fam["_m"]).astype(int)  # les sœurs seulement
    fam["famille_societes_avec_offre"] = (fam["_n_with"] - (fam["_m"] > 0)).astype(int)
    keep = fam.assign(siren=fam["siren"].astype(str)).set_index("siren")
    key = out["siren"].astype(str)
    out["famille_nom"] = key.map(keep["famille_nom"])
    for c in ("famille_offres", "famille_societes_avec_offre"):
        out[c] = key.map(keep[c]).fillna(0).astype(int)
    return out


def family_signal(r) -> str:
    """Phrase courte pour la liste, la carte et la fiche (chaîne vide si rien à signaler)."""
    n = int(r.get("famille_offres", 0) or 0)
    if n <= 0:
        return ""
    name = str(r.get("famille_nom") or "son groupe")
    return f"Groupe {name} : {n} offre{'s' if n > 1 else ''} déjà publiée{'s' if n > 1 else ''}"
