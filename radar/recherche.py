"""Recherche d'entreprises par nom, SIREN ou SIRET (page « Entreprises »).

Tolérante aux fautes et aux accents (rapidfuzz) : « sopra steira » trouve « SOPRA STERIA ».
Cherche dans le nom de l'entreprise, le nom de l'établissement et le sigle, sur tout le
référentiel (data/processed/entreprises.parquet, ~406 000 établissements).

    index = load_index()                       # une fois (≈ 1 s), à mettre en cache
    hits = search_companies(index, "sopra steria", commune="rennes")
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import duckdb
import pandas as pd
from rapidfuzz import fuzz

from radar.config import FILES

INDEX_COLS = [
    "siret",
    "siren",
    "nom",
    "nom_etablissement",
    "sigle",
    "commune",
    "code_postal",
    "naf_libelle",
    "tranche_libelle",
    "effectif_estime",
    "siege",
    "procedure_type",
]
MIN_SCORE = 75  # en dessous, la correspondance est trop lointaine


def normalize(text) -> str:
    """Minuscules, sans accents ni ponctuation : « Société Générale » → « societe generale »."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    t = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def load_index(path: Path = FILES["entreprises"]) -> pd.DataFrame:
    """Colonnes utiles à la recherche + `_cle` (noms normalisés) et `_commune` (normalisée)."""
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=[*INDEX_COLS, "_cle", "_commune", "_n_sites"])
    con = duckdb.connect()
    cols = {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{path}'").fetchall()}
    keep = [c for c in INDEX_COLS if c in cols]
    df = con.execute(f"SELECT {', '.join(keep)} FROM '{path}'").df().reindex(columns=INDEX_COLS)
    names = df["nom"].map(normalize)
    for extra in ("nom_etablissement", "sigle"):
        other = df[extra].map(normalize)
        names = names.where(other.eq("") | other.eq(names), names + " " + other)
    df["_cle"] = names
    df["_commune"] = df["commune"].map(normalize)
    df["_n_sites"] = df.groupby("siren")["siret"].transform("size")  # sites de l'entreprise (T57)
    return df


def _token_score(query_tokens: list[str], key: str) -> float:
    """Moyenne, sur les mots recherchés, de la meilleure ressemblance avec un mot du nom.

    « sopra steira » / « sopra steria group » → (100 + 83) / 2 ≈ 92 ; « sopra » seul → ≈ 68.
    """
    words = key.split()
    if not words:
        return 0.0
    return sum(max(fuzz.ratio(t, w) for w in words) for t in query_tokens) / len(query_tokens)


def _scored(cand: pd.DataFrame, tokens: list[str]) -> pd.DataFrame:
    """Note fine mot par mot ; garde les candidats au-dessus de MIN_SCORE."""
    out = cand.assign(_score=cand["_cle"].map(lambda k: _token_score(tokens, k)))
    return out[out["_score"] >= MIN_SCORE]


def search_companies(
    index: pd.DataFrame, query: str, commune: str = "", limit: int = 50
) -> pd.DataFrame:
    """Établissements qui correspondent à la recherche, les plus proches d'abord (`_score`).

    `query` : nom (tolérant aux fautes), ou SIREN (9 chiffres) / SIRET (14 chiffres).
    `commune` : filtre facultatif sur le début du nom de la commune ou du code postal.
    """
    empty = index.iloc[0:0].assign(_score=pd.Series(dtype=float))
    q = query.strip()
    if index.empty or not q:
        return empty
    digits = re.sub(r"\s", "", q)
    if digits.isdigit() and len(digits) in (9, 14):
        col = "siren" if len(digits) == 9 else "siret"
        out = index[index[col] == digits].assign(_score=100.0)
    else:
        pool = index
        if commune.strip():
            c = normalize(commune)
            pool = pool[
                pool["_commune"].str.startswith(c)
                | pool["code_postal"].fillna("").astype(str).str.startswith(commune.strip())
            ]
        tokens = normalize(q).split()
        if not tokens:
            return empty
        # 1. présélection rapide : chaque mot recherché (ses 3 premières lettres) est dans le nom
        strict = pool
        for t in tokens:
            strict = strict[strict["_cle"].str.contains(t[:3], regex=False)]
        out = _scored(strict, tokens)
        # 2. rien de proche (faute dans les premières lettres d'un mot) : il suffit qu'UN mot
        #    soit reconnu pour être candidat
        if out.empty:
            any_token = pd.Series(False, index=pool.index)
            for t in tokens:
                any_token |= pool["_cle"].str.contains(t[:3], regex=False)
            out = _scored(pool[any_token], tokens)
    out = out.assign(_eff=out["effectif_estime"].fillna(0))
    out = out.sort_values(["_score", "_eff"], ascending=[False, False])
    return out.drop(columns=["_eff"]).head(limit).reset_index(drop=True)


def with_companies(hits: pd.DataFrame, max_companies: int = 10) -> pd.DataFrame:
    """Résultats regroupés (T57) : d'abord une ligne « entreprise » par SIREN qui a plusieurs
    sites (toute l'entreprise), dans l'ordre des meilleurs résultats, puis les sites un par un.

    Colonne `_type` : "entreprise" ou "site". Une entreprise à un seul site n'a que sa ligne site.
    """
    if hits.empty:
        return hits.assign(_type=pd.Series(dtype=str))
    multi = hits[hits["_n_sites"].fillna(1) > 1]
    companies = multi.drop_duplicates("siren").head(max_companies).assign(_type="entreprise")
    return pd.concat([companies, hits.assign(_type="site")], ignore_index=True)
