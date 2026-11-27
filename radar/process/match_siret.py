"""Rapprochement des offres (nom d'entreprise + position) avec un établissement SIRENE (T21).

Adzuna ne fournit que le nom affiché de l'entreprise. Étapes, par ordre de confiance :
1. **intermédiaire** : plateformes, sites d'emploi, cabinets de recrutement, intérim → pas de
   SIRET (sinon Collective.work deviendrait « l'entreprise la plus data de France ») ;
2. **exact** : nom normalisé identique au nom d'une unité légale ;
3. **sigle** : nom de l'offre = sigle d'une **grande entreprise** (EDF, CEA…) ;
   puis (T25) **alias** : morceau du nom légal (« … - S.F.R ») et **enseigne** d'établissement ;
   le nom sans espaces compte comme exact (« AirFrance ») ; entre homonymes, on préfère ETI / GE ;
4. **prefixe** : le nom de l'offre est le début du nom légal (« Capgemini » →
   « CAPGEMINI TECHNOLOGY SERVICES ») ;
5. **flou** : similarité rapidfuzz ≥ FUZZY_CUTOFF, accepté seulement à moins de FAR_KM.
Parmi les établissements candidats, on garde **le plus proche** de l'offre (à 1 km près, le plus
gros). Au-delà de FAR_KM : suffixe `_loin`, accepté pour exact/sigle, accepté pour prefixe
seulement si l'entreprise est une ETI/GE (sinon homonymes fréquents), refusé pour flou.

Vérification manuelle (2026-11-27, échantillons de 10 noms par méthode) : exact et prefixe
≈ justes ; exact_loin ≈ 7/10 (bonne entreprise, souvent son siège) ; flou ≈ 5/10 avant
resserrement ; flou_loin ≈ 0/10 → refusé.
"""

from __future__ import annotations

import bisect
import re
import unicodedata

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process

FUZZY_CUTOFF = 94
FAR_KM = 50
BIG = ("GE", "ETI")

# Formes juridiques et mots vides. « france » et « societe » sont gardés : les retirer
# confondait « Air France » et « France Air ».
STOPWORDS = {
    "sa", "sas", "sasu", "sarl", "eurl", "sca", "se", "snc", "sci", "scop", "gie", "ste",
    "group", "groupe", "holding", "the", "et", "de", "du", "des", "la", "le", "les", "l", "d",
    "and", "co", "cie", "inc", "ltd", "llc", "gmbh", "spa", "bv", "h", "f",
}  # fmt: skip

# Plateformes, sites d'emploi, cabinets de recrutement, intérim, portage (noms normalisés).
# Reconnu si le nom normalisé est égal à l'un d'eux ou commence par « <nom> ».
# À compléter en regardant les plus gros émetteurs non rapprochés (match_report).
INTERMEDIARIES = {
    "collective work", "forums talents handicap", "talents handicap", "groupe talents handicap",
    "free work", "direct emploi", "france travail", "pole emploi", "externatic", "michael page",
    "page personnel", "page group", "hays", "robert half", "adecco", "randstad", "manpower",
    "manpowergroup", "synergie", "crit", "proman", "start people", "expectra", "fed it",
    "fed finance", "fed group", "fed", "walters people", "robert walters", "spring", "kicklox",
    "malt", "creme de la creme", "freelance com", "lincoln", "talents it", "rm staffing",
    "hellowork", "indeed", "jobteaser", "welcome to jungle", "apec", "cadremploi", "meteojob",
    "monster", "keljob", "regionsjob", "jobijoba", "staffme", "side", "gojob", "qapa",
    "jobposting", "job posting", "choisir service public", "place emploi public",
    "l industrie recrute", "industrie recrute", "mon consultant independant", "adsearch",
    "confidentiel", "entreprise confidentielle", "confidential", "anonyme", "client final",
    "nous recrutons", "recrutement",
}  # fmt: skip
INTERMEDIARY_PATTERNS = re.compile(
    r"\b(recrutement|recruitment|recruiting|staffing|interim|intérim|executive search|"
    r"headhunt\w*|chasseurs? de t[eê]tes|portage salarial|job ?board)\b",
    re.IGNORECASE,
)
# NAF des activités de placement / mise à disposition de personnel
INTERMEDIARY_NAF_PREFIX = ("78.",)


_DOTTED_ACRONYM = re.compile(r"\b(?:[A-Za-z]\.){1,}[A-Za-z]\b\.?")


def normalize(name: str | None) -> str:
    """Minuscules, sans accents ni ponctuation, sans formes juridiques ni mots vides."""
    if not isinstance(name, str) or not name:
        return ""
    # Sigles à points recollés AVANT de retirer les mots d'une lettre (« S.F.R » → « SFR » ;
    # sinon le « F » disparaît avec les « H/F »).
    name = _DOTTED_ACRONYM.sub(lambda m: m.group(0).replace(".", ""), name)
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", " ", s.lower())
    return " ".join(t for t in s.split() if t not in STOPWORDS)


_SPACED_LETTERS = re.compile(r"\b(?:[a-z0-9] )+[a-z0-9]\b")
_NAME_PARTS = re.compile(r"\s[-–]\s|[()]")


def collapse_letters(norm: str) -> str:
    """« s f r » → « sfr » (sigles écrits avec des points : « S.F.R »)."""
    return _SPACED_LETTERS.sub(lambda m: m.group(0).replace(" ", ""), norm)


def name_parts(name: str | None) -> set[str]:
    """Morceaux d'un nom légal : « SOCIETE FRANCAISE DU RADIOTELEPHONE - S.F.R » → {« sfr »}."""
    if not isinstance(name, str):
        return set()
    parts = {collapse_letters(normalize(p)) for p in _NAME_PARTS.split(name)}
    return {p for p in parts if len(p) >= 3} - {collapse_letters(normalize(name))}


def is_intermediary(raw_name: str | None, norm: str) -> bool:
    if not norm:
        return False
    if norm in INTERMEDIARIES or any(norm.startswith(i + " ") for i in INTERMEDIARIES):
        return True
    return isinstance(raw_name, str) and bool(INTERMEDIARY_PATTERNS.search(raw_name))


def _haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


class SireneIndex:
    """Index des établissements par nom normalisé et par sigle de l'unité légale."""

    def __init__(self, ent: pd.DataFrame):
        ent = ent.dropna(subset=["lat", "lon"]).reset_index(drop=True)
        self.ent = ent
        self.lat = ent["lat"].to_numpy(float)
        self.lon = ent["lon"].to_numpy(float)
        self.size = ent["effectif_estime"].fillna(0).to_numpy(float)
        self.naf = ent["naf"].fillna("").to_numpy()
        self.big = ent["categorie"].isin(BIG).to_numpy()
        norms = ent["nom"].map(normalize)
        self.by_name = {k: v.to_numpy() for k, v in norms.groupby(norms).groups.items() if k}
        self.names_sorted = sorted(self.by_name)
        # Variantes (T25) : nom sans espaces (« AirFrance »), morceaux du nom légal
        # (« … - S.F.R »), enseigne de l'établissement (« Ouest France », « agap2 »).
        nospace = norms.str.replace(" ", "", regex=False)
        self.by_nospace = {
            k: v.to_numpy() for k, v in nospace.groupby(nospace).groups.items() if len(k) >= 5
        }
        alias: dict[str, list[int]] = {}
        for nom, rows in ent.groupby("nom").groups.items():
            for part in name_parts(nom):
                alias.setdefault(part, []).extend(rows)
        self.by_alias = {k: np.asarray(v) for k, v in alias.items()}
        self.by_enseigne: dict[str, np.ndarray] = {}
        if "nom_etablissement" in ent:
            ens = ent["nom_etablissement"].map(normalize).map(collapse_letters)
            self.by_enseigne = {
                k: v.to_numpy() for k, v in ens.groupby(ens).groups.items() if len(k) >= 3
            }
        # Sigles : seulement l'unité légale « GE » la plus grosse portant ce sigle.
        self.by_sigle: dict[str, np.ndarray] = {}
        if "sigle" in ent:
            ge = ent[ent["categorie"].eq("GE") & ent["sigle"].notna()]
            sig = ge["sigle"].map(normalize)
            size_by_siren = ge.groupby("siren")["effectif_estime"].sum()
            for s, grp in ge.groupby(sig):
                if len(s) >= 2:
                    top = size_by_siren.loc[grp["siren"].unique()].idxmax()
                    self.by_sigle[s] = grp.index[grp["siren"].eq(top)].to_numpy()

    def _prefer_big(self, idx: np.ndarray) -> np.ndarray:
        """Homonymes : si l'un des candidats est une ETI / GE, on ne garde que ceux-là
        (« Atos » → ATOS, pas une petite société homonyme plus proche)."""
        big = idx[self.big[idx]]
        return big if len(big) else idx

    def candidates(self, norm: str) -> list[tuple[np.ndarray, str, float]]:
        """Candidats (indices, méthode, score) par ordre de confiance. Le rapprochement essaie
        le suivant si le précédent est refusé (« Atos » : la PME homonyme lointaine est refusée,
        le préfixe trouve ATOS FRANCE)."""
        out: list[tuple[np.ndarray, str, float]] = []
        if norm in self.by_name:
            out.append((self._prefer_big(self.by_name[norm]), "exact", 100.0))
        ns = norm.replace(" ", "")
        if ns in self.by_nospace and ns != norm:
            out.append((self._prefer_big(self.by_nospace[ns]), "exact", 99.0))
        if norm in self.by_sigle:
            out.append((self.by_sigle[norm], "sigle", 98.0))
        key = collapse_letters(norm)
        if key in self.by_alias:
            out.append((self._prefer_big(self.by_alias[key]), "alias", 97.0))
        if key in self.by_enseigne:
            out.append((self._prefer_big(self.by_enseigne[key]), "enseigne", 96.0))
        if len(norm) >= 3:
            start = bisect.bisect_left(self.names_sorted, norm + " ")
            pref = []
            for name in self.names_sorted[start:]:
                if not name.startswith(norm + " "):
                    break
                pref.append(self.by_name[name])
            if pref:
                idx = np.concatenate(pref)
                if len(norm) == 3:  # sigles courts (CGI…) : seulement les ETI / GE
                    idx = idx[self.big[idx]]
                if len(idx):
                    out.append((idx, "prefixe", 95.0))
        if len(norm) >= 5 and not out:
            hit = process.extractOne(
                norm, self.names_sorted, scorer=fuzz.ratio, score_cutoff=FUZZY_CUTOFF
            )
            if hit:
                out.append((self.by_name[hit[0]], "flou", float(hit[1])))
        return out

    def nearest(self, idx: np.ndarray, lat: float, lon: float) -> tuple[int, float]:
        """Établissement le plus proche (à 1 km près, le plus gros)."""
        if np.isnan(lat) or np.isnan(lon):
            return int(idx[np.argmax(self.size[idx])]), float("nan")
        d = _haversine_km(lat, lon, self.lat[idx], self.lon[idx])
        near = d <= d.min() + 1.0
        k = np.flatnonzero(near)[np.argmax(self.size[idx[near]])]
        return int(idx[k]), float(d[k])


def _accept(methode: str, far: bool, big: bool, norm: str) -> bool:
    """Loin de l'offre, seuls les noms distinctifs ou les grandes entreprises sont crédibles."""
    if not far:
        return True
    if methode == "sigle":
        return True
    if methode == "exact":
        return big or len(norm) >= 7  # « le casino » à 300 km : homonyme probable
    if methode in ("alias", "enseigne"):
        return False  # vérifié à la main : ≈ 1 sur 2 juste au-delà de 50 km (GMF, CLS…)
    return methode == "prefixe" and big and len(norm) >= 4  # « CLS » → CLS RÉMY COINTREAU


def match_offers(offers: pd.DataFrame, ent: pd.DataFrame) -> pd.DataFrame:
    """Ajoute siret_match, siren_match, match_score, match_methode, match_confiance,
    match_distance_km, intermediaire. Une offre non rapprochée garde siret_match manquant."""
    index = SireneIndex(ent)
    out = offers.copy()
    out["_norm"] = out["entreprise_nom"].map(normalize)
    keys = out[["_norm", "entreprise_nom", "lat", "lon"]].drop_duplicates()

    cache: dict[str, tuple[np.ndarray, str, float]] = {}
    records = []
    for norm, raw, lat, lon in keys.itertuples(index=False):
        rec = {"_norm": norm, "entreprise_nom": raw, "lat": lat, "lon": lon}
        if is_intermediary(raw, norm):
            records.append(rec | {"match_methode": "intermediaire", "match_score": 0.0})
            continue
        if norm not in cache:
            cache[norm] = index.candidates(norm) if norm else []
        chosen = None
        for idx, methode, score in cache[norm]:
            best, dist = index.nearest(idx, float(lat), float(lon))
            far = dist == dist and dist > FAR_KM  # dist == dist : pas NaN
            if _accept(methode, far, bool(index.big[best]), norm):
                chosen = (best, dist, far, methode, score)
                break
        if chosen is None:
            records.append(rec | {"match_methode": "aucun", "match_score": 0.0})
            continue
        best, dist, far, methode, score = chosen
        if index.naf[best].startswith(INTERMEDIARY_NAF_PREFIX):
            records.append(rec | {"match_methode": "intermediaire", "match_score": score})
            continue
        e = index.ent.iloc[best]
        records.append(
            rec
            | {
                "siret_match": e["siret"],
                "siren_match": e["siren"],
                "match_methode": methode + ("_loin" if far else ""),
                "match_confiance": "moyenne" if far or methode == "flou" else "haute",
                "match_score": score,
                "match_distance_km": round(dist, 1) if dist == dist else None,
            }
        )
    m = pd.DataFrame.from_records(records)
    for col in ("siret_match", "siren_match", "match_confiance", "match_distance_km"):
        if col not in m:
            m[col] = None
    out = out.merge(m, on=["_norm", "entreprise_nom", "lat", "lon"], how="left")
    out["intermediaire"] = out["match_methode"].eq("intermediaire")
    return out.drop(columns="_norm")


def match_report(df: pd.DataFrame) -> pd.DataFrame:
    """Taux de rapprochement par méthode, en offres et en entreprises (noms distincts)."""
    r = df.groupby("match_methode").agg(
        offres=("offre_id", "size"), entreprises=("entreprise_nom", "nunique")
    )
    r["part_offres"] = (r["offres"] / r["offres"].sum()).round(3)
    return r.sort_values("offres", ascending=False)
