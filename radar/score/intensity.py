"""Intensité de recrutement dans un domaine : modèle gamma-Poisson, bayésien empirique (T30/T31).

Pour chaque entreprise i (SIREN) du secteur s (division NAF de son plus gros établissement,
lissée vers sa section) :

    k_i | λ_i ~ Poisson(λ_i · E_i)        k_i : offres du domaine observées
    λ_i       ~ Gamma(α_s, β_s)            λ_i : offres du domaine pour 100 salariés
                                            E_i : exposition = Σ effectif × couverture / 100

La couverture (part des offres de la région réellement collectées, ∈ [0, 1]) corrige le fait
que la collecte ne couvre pas toute la France : une entreprise d'une région non collectée a
E_i = 0 et reçoit exactement l'a priori de son secteur (pas « 0 offre »).

Pourquoi pas le bêta-binomial (part d'offres du domaine) : la collecte Adzuna ne porte que sur
la requête « data », donc le dénominateur « toutes les offres de l'entreprise » est inconnu.

A priori par secteur estimé par la méthode des moments de Clayton & Kaldor (1987) :
    m = Σk / ΣE,  v = [Σ E_i (k_i/E_i − m)² − (n − 1) m] / [ΣE − ΣE² / ΣE]
    α = m² / v,   β = m / v
Moyenne de secteur m lissée vers la moyenne globale (sinon un secteur sans aucune offre aurait
m = 0 et des intervalles dégénérés) ; v plancher → fort rétrécissement si la dispersion
entre entreprises n'est pas détectable.

A posteriori : λ_i | k_i ~ Gamma(α_s + k_i, β_s + E_i).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

SECTOR_SMOOTHING = 1000.0  # poids (en centaines de salariés couverts) de la moyenne globale
MIN_PRIOR_SHAPE = 0.05  # α minimal : a priori très diffus si la dispersion est énorme
MAX_PRIOR_SHAPE = 50.0  # α maximal : a priori très concentré si aucune dispersion détectée
CI_LEVEL = 0.90


@dataclass(frozen=True)
class Prior:
    alpha: float
    beta: float

    @property
    def mean(self) -> float:
        return self.alpha / self.beta


def clayton_kaldor(k: np.ndarray, e: np.ndarray, m_global: float, smoothing: float) -> Prior:
    """A priori Gamma(α, β) d'un groupe, par la méthode des moments de Clayton & Kaldor."""
    k, e = np.asarray(k, float), np.asarray(e, float)
    keep = e > 0
    k, e = k[keep], e[keep]
    n, e_sum = len(e), e.sum()
    m = (k.sum() + smoothing * m_global) / (e_sum + smoothing)
    if n >= 2 and e_sum > 0:
        s = np.sum(e * (k / e - m) ** 2)
        denom = e_sum - np.sum(e**2) / e_sum
        v = (s - (n - 1) * m) / denom if denom > 0 else 0.0
    else:
        v = 0.0
    alpha = m**2 / v if v > 0 else MAX_PRIOR_SHAPE
    alpha = float(np.clip(alpha, MIN_PRIOR_SHAPE, MAX_PRIOR_SHAPE))
    return Prior(alpha=alpha, beta=alpha / m)


def fit_priors(
    df: pd.DataFrame, group: str = "naf_division", parent: str | None = "naf_section"
) -> dict[str, Prior]:
    """Un a priori par groupe. `df` : une ligne par entreprise, colonnes k, E, <group>, <parent>.

    Hiérarchie à deux niveaux : la moyenne d'un groupe (division NAF) est lissée vers celle de
    son parent (section NAF), elle-même lissée vers la moyenne globale. Une division sans
    offre (ex. 59 « cinéma » dans la section J) ne reçoit donc pas l'a priori de la
    programmation informatique.
    """
    m_global = df["k"].sum() / df["E"].sum()
    parent_mean: dict = {}
    if parent:
        for p, d in df.groupby(parent, dropna=False):
            parent_mean[p] = clayton_kaldor(d["k"], d["E"], m_global, SECTOR_SMOOTHING).mean
    priors = {}
    for g, d in df.groupby(group, dropna=False):
        m_ref = parent_mean.get(d[parent].iloc[0], m_global) if parent else m_global
        priors[g] = clayton_kaldor(d["k"].to_numpy(), d["E"].to_numpy(), m_ref, SECTOR_SMOOTHING)
    priors["__global__"] = clayton_kaldor(df["k"], df["E"], m_global, 0.0)
    return priors


def posterior(
    df: pd.DataFrame, priors: dict[str, Prior], group: str = "naf_division"
) -> pd.DataFrame:
    """Ajoute prior_moyenne, intensite_post, intensite_ic_bas, intensite_ic_haut (pour 100 sal.)."""
    out = df.copy()
    glob = priors["__global__"]
    a0 = out[group].map(lambda g: priors.get(g, glob).alpha).astype(float)
    b0 = out[group].map(lambda g: priors.get(g, glob).beta).astype(float)
    a, b = a0 + out["k"], b0 + out["E"]
    q = (1 - CI_LEVEL) / 2
    out["prior_moyenne"] = a0 / b0
    out["intensite_post"] = a / b
    out["intensite_ic_bas"] = stats.gamma.ppf(q, a, scale=1 / b)
    out["intensite_ic_haut"] = stats.gamma.ppf(1 - q, a, scale=1 / b)
    return out
