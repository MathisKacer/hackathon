"""Fiche entreprise (T43) : tout ce qu'on sait d'un établissement de la couche orange.

Données seulement (testable sans Streamlit) ; l'affichage est dans app/fiche_ui.py.
Chaque fonction lit UN établissement avec DuckDB (rapide, sans charger la France entière)
et renvoie un résultat vide si le fichier manque : la fiche marche avec les données partielles.

    company = load_company(siret)                 # ligne complète de entreprises.parquet
    offers = company_offers(siren, siret)         # offres rapprochées (offres.parquet)
    history = bodacc_history(siren)               # jugements BODACC (cache T23)
    proof = evidence(row)                         # niveau de preuve du besoin dans le domaine

Coordination avec T32 (@mathis) : la fiche affiche la colonne `explication` si elle existe.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote_plus

import duckdb
import pandas as pd

from radar.collect.bodacc import RAW_FILE as BODACC_FILE
from radar.collect.bodacc import _parse_jugement, classify_nature
from radar.config import FILES
from radar.niveau import levels_label, offer_levels

ANNUAIRE_URL = "https://annuaire-entreprises.data.gouv.fr/etablissement/{siret}"
OSM_URL = "https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=17/{lat}/{lon}"
OFFERS_SHOWN = 10


def _columns(con: duckdb.DuckDBPyConnection, path: Path) -> set[str]:
    return {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{path}'").fetchall()}


def load_company(siret: str, path: Path = FILES["entreprises"]) -> pd.Series | None:
    """Toutes les colonnes de entreprises.parquet pour un SIRET (None si absent)."""
    path = Path(path)
    if not path.exists():
        return None
    df = duckdb.connect().execute(f"SELECT * FROM '{path}' WHERE siret = ?", [str(siret)]).df()
    return None if df.empty else df.iloc[0]


def company_offers(
    siren: str | None,
    siret: str | None = None,
    path: Path = FILES["offres"],
    limit: int = OFFERS_SHOWN,
) -> pd.DataFrame:
    """Offres de l'entreprise (toute l'entreprise, par SIREN), les plus récentes d'abord.

    Rattachement : `siren_match` (T21) ou SIRET donné par la source (La bonne alternance).
    `niveau` (T67) : niveau d'études attendu, « Bac+5 »… ou « Non précisé ».
    """
    cols_out = [
        "date_publication", "titre", "contrat", "niveau", "domaine", "commune", "source", "url"
    ]  # fmt: skip
    path = Path(path)
    if not path.exists() or not (siren or siret):
        return pd.DataFrame(columns=cols_out)
    con = duckdb.connect()
    cols = _columns(con, path)
    conds, params = [], []
    if siren and "siren_match" in cols:
        conds.append("siren_match = ?")
        params.append(str(siren))
    if siret and "siret" in cols:
        conds.append("siret = ?")
        params.append(str(siret))
    if siret and "siret_match" in cols:
        conds.append("siret_match = ?")
        params.append(str(siret))
    if not conds:
        return pd.DataFrame(columns=cols_out)
    # description et niveau_diplome : seulement pour calculer `niveau` (retirées ensuite)
    keep = [c for c in cols_out + ["description", "niveau_diplome"] if c in cols]
    where = " OR ".join(conds)
    if "intermediaire" in cols:  # offres d'intermédiaires : pas l'employeur (T21)
        where = f"({where}) AND NOT coalesce(intermediaire, false)"
    order = "ORDER BY date_publication DESC NULLS LAST" if "date_publication" in cols else ""
    df = con.execute(
        f"SELECT DISTINCT {', '.join(keep)} FROM '{path}' WHERE {where} {order} LIMIT {int(limit)}",
        params,
    ).df()
    df["niveau"] = [levels_label(offer_levels(r)) for r in df.to_dict("records")]
    return df.reindex(columns=cols_out)


def bodacc_history(siren: str | None, path: Path = BODACC_FILE) -> pd.DataFrame:
    """Annonces BODACC de procédures collectives de l'entreprise, les plus récentes d'abord.

    Colonnes : date, situation (sauvegarde / redressement / liquidation / plan / fin / autre),
    nature (texte du jugement), url. Vide si pas d'annonce ou cache BODACC absent.
    """
    cols_out = ["date", "situation", "nature", "url"]
    path = Path(path)
    if not siren or not path.exists():
        return pd.DataFrame(columns=cols_out)
    raw = (
        duckdb.connect()
        .execute(
            f"SELECT dateparution, typeavis, jugement, url_complete FROM '{path}' "
            "WHERE registre LIKE ? AND coalesce(typeavis, '') <> 'annulation'",
            [f"{siren}%"],
        )
        .df()
    )
    if raw.empty:
        return pd.DataFrame(columns=cols_out)
    parsed = raw["jugement"].map(_parse_jugement)
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(parsed.str[1], errors="coerce").fillna(
                pd.to_datetime(raw["dateparution"], errors="coerce")
            ),
            "nature": parsed.str[0],
            "url": raw["url_complete"],
        }
    )
    out["situation"] = out["nature"].map(classify_nature).fillna("autre")
    return out.sort_values("date", ascending=False).reset_index(drop=True)[cols_out]


def _num(row: pd.Series, *names: str) -> float | None:
    for n in names:
        v = row.get(n)
        if v is not None and pd.notna(v):
            return float(v)
    return None


def evidence(row: pd.Series) -> dict:
    """Niveau de preuve du besoin dans le domaine (T44 en version fiche).

    Renvoie : n_offres, n_stage, n_alternance (entreprise entière si disponible), intensite et
    son intervalle crédible (offres du domaine pour 100 salariés), moyenne du secteur,
    couverture de la collecte, et un niveau lisible : élevé / moyen / faible / non collecté.
    """
    n = _num(row, "n_offres_domaine_siren", "n_offres_domaine") or 0
    couverture = _num(row, "couverture")
    if couverture is not None and couverture == 0:
        level = "non collecté"
        why = "zone où les offres n'ont pas été collectées : estimation d'après le secteur"
    elif n >= 5:
        level, why = "élevé", f"{int(n)} offres du domaine observées"
    elif n >= 1:
        level, why = (
            "moyen",
            f"{int(n)} offre{'s' if n > 1 else ''} du domaine observée{'s' if n > 1 else ''}",
        )
    else:
        level = "faible"
        why = "aucune offre du domaine observée : besoin estimé d'après le secteur et la taille"
    return {
        "n_offres": int(n),
        "n_stage": int(_num(row, "n_stage_domaine_siren", "n_stage_domaine") or 0),
        "n_alternance": int(_num(row, "n_alternance_domaine_siren", "n_alternance_domaine") or 0),
        "intensite": _num(row, "intensite_post"),
        "ic_bas": _num(row, "intensite_ic_bas"),
        "ic_haut": _num(row, "intensite_ic_haut"),
        "moyenne_secteur": _num(row, "prior_moyenne"),
        "couverture": couverture,
        "niveau": level,
        "explication_niveau": why,
    }


def contact_searches(name: str | None, commune: str | None = None) -> dict[str, str]:
    """T88 : recherches pré-remplies pour trouver comment contacter une entreprise.

    Aucune de nos données ne donne l'adresse des sites web (le champ `site_web` de La bonne
    alternance est vide) : on propose des recherches avec le nom de l'entreprise.
    Libellé du bouton → adresse. Vide si on n'a pas de nom.
    """
    name = " ".join(str(name or "").split())
    if not name:
        return {}
    city = " ".join(str(commune or "").split()).title()
    web = "https://www.google.com/search?q="
    return {
        "Son site web": web + quote_plus(" ".join(x for x in (name, city, "site officiel") if x)),
        "Sa page recrutement": web + quote_plus(f"{name} recrutement candidature spontanée"),
        "Sur LinkedIn": "https://www.linkedin.com/search/results/companies/?keywords="
        + quote_plus(name),
    }


def links(row: pd.Series) -> dict[str, str]:
    """Liens utiles : Annuaire des entreprises, carte, annonce BODACC (si procédure)."""
    out = {}
    if row.get("siret"):
        out["Annuaire des entreprises"] = ANNUAIRE_URL.format(siret=row["siret"])
    lat, lon = row.get("lat"), row.get("lon")
    if lat is not None and lon is not None and pd.notna(lat) and pd.notna(lon):
        out["Carte (OpenStreetMap)"] = OSM_URL.format(lat=f"{lat:.5f}", lon=f"{lon:.5f}")
    url = row.get("procedure_url")
    if isinstance(url, str) and url:
        out["Annonce BODACC"] = url
    return out


def load_scores(siret: str, domaine: str, path: Path = FILES["scores"]) -> pd.Series | None:
    """Indicateurs du score pour un établissement et un domaine (None si non noté).

    Sert à la fiche ouverte depuis la recherche d'entreprises (pas de distance ni de poids :
    pas de score final, mais le besoin dans le domaine et le niveau de preuve).
    """
    path = Path(path)
    if not path.exists():
        return None
    df = (
        duckdb.connect()
        .execute(f"SELECT * FROM '{path}' WHERE siret = ? AND domaine = ?", [str(siret), domaine])
        .df()
    )
    return None if df.empty else df.iloc[0]


LBB_MEDIAN_POTENTIEL = 2.8  # médiane de `lbb_potentiel` des établissements signalés (D27)


def hiring_signal(row: pd.Series) -> dict | None:
    """Source du potentiel d'embauche (T38, D27).

    {"lbb": True, "potentiel": 5.2} si La Bonne Boîte (France Travail) signale l'établissement ;
    {"lbb": False} si c'est une estimation (offres du secteur × effectif) ; None si pas de score.
    """
    from radar.spontaneous import LBB_SOURCE  # import local : évite un cycle d'imports

    src = row.get("c_embauche_source")
    if src is None or (isinstance(src, float) and pd.isna(src)):
        return None
    if src == LBB_SOURCE:
        pot = row.get("lbb_potentiel")
        return {"lbb": True, "potentiel": float(pot) if pot is not None and pd.notna(pot) else None}
    return {"lbb": False}


# --- Niveau entreprise (SIREN) : tous les sites d'une même société (T57) ------------------

ANNUAIRE_ENTREPRISE_URL = "https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}"
SITE_COLS = [
    "siret",
    "nom",
    "nom_etablissement",
    "adresse",
    "code_postal",
    "commune",
    "tranche_libelle",
    "tranche_effectif",
    "tranche_entreprise_libelle",
    "annee_effectif_entreprise",
    "effectif_estime",
    "siege",
    "diffusion_partielle",
    "lat",
    "lon",
    "naf_libelle",
    "categorie",
    "sigle",
    "procedure_type",
    "procedure_date",
    "procedure_url",
]


def company_sites(
    siren: str,
    lat: float | None = None,
    lon: float | None = None,
    path: Path = FILES["entreprises"],
) -> pd.DataFrame:
    """Sites (établissements ≥ 10 salariés) d'une entreprise, les plus proches d'abord si une
    position est donnée (`distance_km`), sinon le siège puis les plus gros."""
    path = Path(path)
    if not path.exists() or not siren:
        return pd.DataFrame(columns=[*SITE_COLS, "distance_km"])
    con = duckdb.connect()
    keep = [c for c in SITE_COLS if c in _columns(con, path)]
    df = (
        con.execute(f"SELECT {', '.join(keep)} FROM '{path}' WHERE siren = ?", [str(siren)])
        .df()
        .reindex(columns=SITE_COLS)
    )
    if lat is not None and lon is not None:
        from radar.spontaneous import haversine_km

        df["distance_km"] = haversine_km(lat, lon, df["lat"], df["lon"])
        return df.sort_values("distance_km", na_position="last").reset_index(drop=True)
    df["distance_km"] = float("nan")
    df["_siege"] = df["siege"].fillna(False).astype(bool)
    df = df.sort_values(["_siege", "effectif_estime"], ascending=[False, False], na_position="last")
    return df.drop(columns="_siege").reset_index(drop=True)


def company_summary(sites: pd.DataFrame, siren: str) -> dict:
    """Résumé d'une entreprise à partir de ses sites (sortie de company_sites)."""
    if sites.empty:
        return {"siren": siren, "nom": None, "n_sites": 0}
    siege = sites[sites["siege"].fillna(False).astype(bool)]
    ref = siege.iloc[0] if not siege.empty else sites.iloc[0]
    eff = sites["effectif_estime"].dropna()
    return {
        "siren": siren,
        "nom": ref.get("nom"),
        "sigle": ref.get("sigle") if pd.notna(ref.get("sigle")) else None,
        "categorie": ref.get("categorie") if pd.notna(ref.get("categorie")) else None,
        "activite": ref.get("naf_libelle") if pd.notna(ref.get("naf_libelle")) else None,
        "n_sites": len(sites),
        "effectif_total": int(eff.sum()) if not eff.empty else None,  # estimation (T73)
        # Tranche officielle de l'entreprise entière (SIRENE, unité légale), T73
        "tranche_entreprise": ref.get("tranche_entreprise_libelle")
        if pd.notna(ref.get("tranche_entreprise_libelle"))
        else None,
        "annee_effectif_entreprise": int(ref["annee_effectif_entreprise"])
        if pd.notna(ref.get("annee_effectif_entreprise"))
        else None,
        "siege_commune": ref.get("commune") if not siege.empty else None,
        "procedure_type": ref.get("procedure_type")
        if pd.notna(ref.get("procedure_type"))
        else None,
        "procedure_date": ref.get("procedure_date"),
        "url_annuaire": ANNUAIRE_ENTREPRISE_URL.format(siren=siren),
    }
