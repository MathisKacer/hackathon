"""T28 — Composante `c_embauche` : La Bonne Boîte quand elle existe, proxy sinon (D27).

La Bonne Boîte (LBB) ne connaît que ~1 700 établissements pour les métiers data (0,4 % du
référentiel) : elle ne peut pas noter seule tout le monde. Règle :
- un établissement que LBB signale pour un métier du domaine passe DEVANT tous les autres
  (être listé est en soi un signal d'embauche), et ces établissements sont classés entre eux
  par `lbb_potentiel` (le `hiring_potential` de LBB, max sur les métiers du domaine) ;
- les autres gardent l'ordre du proxy `besoin_attendu` (intensité × effectif local, D13),
  dans la partie basse de l'échelle.
Résultat dans [0, 1], comme les autres composantes. `c_embauche_source` dit, ligne par ligne,
d'où vient la valeur : "la_bonne_boite" ou "proxy_besoin_attendu".
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SOURCE_LBB = "la_bonne_boite"
SOURCE_PROXY = "proxy_besoin_attendu"


def _pct(s: pd.Series) -> pd.Series:
    return s.rank(pct=True, method="average")


def _log(s: pd.Series) -> pd.Series:
    from radar.score.build import log_scale  # import local : build importe ce module

    return log_scale(s)


def embauche_component(s: pd.DataFrame, lbb_best: pd.DataFrame | None) -> pd.DataFrame:
    """Ajoute `lbb_potentiel`, `c_embauche`, `c_embauche_source` à `s` (une ligne par siret).

    `s` doit contenir `siret` et `besoin_attendu` ; `lbb_best` vient de
    `radar.collect.lbb.best_by_siret` (colonnes `siret`, `lbb_potentiel`), ou None.
    """
    out = s.drop(columns=["lbb_potentiel"], errors="ignore")
    if lbb_best is not None and len(lbb_best):
        out = out.merge(lbb_best[["siret", "lbb_potentiel"]], on="siret", how="left")
    else:
        out["lbb_potentiel"] = np.nan

    has = out["lbb_potentiel"].notna()
    share_proxy = 1.0 - has.mean()  # part de l'échelle laissée aux établissements sans LBB
    c = pd.Series(np.nan, index=out.index, dtype=float)
    rang = pd.Series(np.nan, index=out.index, dtype=float)
    if (~has).any():
        besoin = out.loc[~has, "besoin_attendu"].fillna(0.0)
        rang[~has] = share_proxy * _pct(besoin)
        c[~has] = share_proxy * _log(besoin)  # D48 : échelle log absolue
    if has.any():
        rang[has] = c[has] = share_proxy + (1.0 - share_proxy) * _pct(out.loc[has, "lbb_potentiel"])
    out["c_embauche"] = c
    out["rang_embauche"] = rang  # ancien rang centile : phrases et modèle de réponse simulé
    out["c_embauche_source"] = np.where(has, SOURCE_LBB, SOURCE_PROXY)
    return out
