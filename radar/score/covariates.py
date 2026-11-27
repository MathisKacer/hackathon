"""T69 — Score v1 : bayésien empirique AVEC covariables (régression binomiale négative).

v0 (D13) : λ_i ~ Gamma(α_s, β_s) avec un a priori par secteur NAF seulement.
v1       : λ_i ~ Gamma(shape = 1/φ, moyenne μ_i),  log μ_i = x_i·β
           k_i | λ_i ~ Poisson(λ_i · E_i)   ⇒   k_i ~ BinNeg(μ_i E_i, φ)
           a posteriori : λ_i | k_i ~ Gamma(1/φ + k_i, 1/(φ μ_i) + E_i)

x_i : division NAF (indicatrices), log effectif, log nb d'établissements, âge, modifications de
capital BODACC (levées de fonds), densité d'entreprises data à proximité, catégorie, ESS, mission.
β : régression de Poisson avec offset log E_i (estimateur convergent de la moyenne même en cas de
surdispersion) ; φ : méthode des moments (régression auxiliaire de Cameron & Trivedi).
Ajustée uniquement sur les entreprises d'une zone collectée (E_i > 0).

Évaluation (`evaluate`) : parmi les établissements que La bonne alternance repère comme
recruteurs d'alternants (tous métiers), retrouver ceux qui recrutent sur un métier du domaine —
étiquette externe, jamais utilisée pour l'estimation, et qui neutralise l'effet « grosse
entreprise qui embauche ». Ajustement sur une moitié des départements, mesure sur l'autre.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import roc_auc_score

CI_LEVEL = 0.90
MIN_DIVISION_SIZE = 300  # divisions plus petites regroupées (« autre »)

NUMERIC = [
    "log_effectif",
    "log_n_etab",
    "log_age",
    "jeune_moins_5_ans",
    "log_modif_capital",
    "augmentation_capital",
    "log_densite_data",
    "ess",
    "societe_mission",
]


def design(f: pd.DataFrame, divisions: list[str] | None = None) -> tuple[pd.DataFrame, list[str]]:
    """Matrice des covariables (une ligne par SIREN). `divisions` : modalités retenues."""
    x = pd.DataFrame(index=f.index)
    x["log_effectif"] = np.log(f["effectif_entreprise"].clip(lower=10))
    x["log_n_etab"] = np.log(f["n_etab"].clip(lower=1))
    x["log_age"] = np.log1p(f["age_ans"])
    x["jeune_moins_5_ans"] = (f["age_ans"] < 5).astype(float)
    x["log_modif_capital"] = np.log1p(f["n_modif_capital"])
    x["augmentation_capital"] = f["augmentation_capital"].fillna(False).astype(float)
    x["log_densite_data"] = np.log1p(f["densite_data"])
    x["ess"] = f["ess"].fillna(False).astype(float)
    x["societe_mission"] = f["societe_mission"].fillna(False).astype(float)
    for c in ("ETI", "GE"):
        x[f"cat_{c}"] = (f["categorie"] == c).astype(float)
    div = f["naf_division"].fillna("?").astype(str)
    if divisions is None:
        counts = div.value_counts()
        divisions = sorted(counts[counts >= MIN_DIVISION_SIZE].index)
    div = div.where(div.isin(divisions), "autre")
    dummies = pd.get_dummies(div, prefix="naf", dtype=float)
    for d in divisions:  # mêmes colonnes à l'ajustement et à la prédiction
        dummies[f"naf_{d}"] = dummies.get(f"naf_{d}", 0.0)
    x = pd.concat([x, dummies[[f"naf_{d}" for d in divisions]]], axis=1)
    return sm.add_constant(x.astype(float), has_constant="add"), divisions


class CovariateModel:
    """Régression de Poisson (offset log E) + dispersion φ par moments → a priori Gamma."""

    def fit(self, f: pd.DataFrame) -> CovariateModel:
        fit_rows = f[f["E"] > 0]
        x, self.divisions = design(fit_rows)
        offset = np.log(fit_rows["E"].to_numpy(float))
        y = fit_rows["k"].to_numpy(float)
        glm = sm.GLM(y, x, family=sm.families.Poisson(), offset=offset)
        self.res = glm.fit(method="lbfgs", maxiter=500)
        mu = np.asarray(self.res.predict(x, offset=offset), dtype=float)
        # Cameron & Trivedi : (y - m)² - y = φ m² + ε  ⇒  φ = Σ m²[(y-m)² - y] / Σ m⁴
        num = np.sum(mu**2 * ((y - mu) ** 2 - y))
        self.phi = float(max(num / np.sum(mu**4), 1e-3))
        return self

    def prior_mean(self, f: pd.DataFrame) -> np.ndarray:
        """μ_i : offres du domaine attendues pour 100 salariés, d'après les covariables."""
        x, _ = design(f, self.divisions)
        return np.exp(x.to_numpy(float) @ self.res.params.reindex(x.columns).fillna(0).to_numpy())

    def posterior(self, f: pd.DataFrame) -> pd.DataFrame:
        mu = self.prior_mean(f)
        a = 1 / self.phi + f["k"].to_numpy(float)
        b = 1 / (self.phi * mu) + f["E"].to_numpy(float)
        q = (1 - CI_LEVEL) / 2
        return pd.DataFrame(
            {
                "prior_moyenne": mu,
                "intensite_post": a / b,
                "intensite_ic_bas": stats.gamma.ppf(q, a, scale=1 / b),
                "intensite_ic_haut": stats.gamma.ppf(1 - q, a, scale=1 / b),
            },
            index=f.index,
        )


def gbm_rate(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Référence non linéaire : arbres boostés, perte de Poisson sur k/E pondérée par E."""
    tr = train[train["E"] > 0]
    xtr, divs = design(tr)
    xte, _ = design(test, divs)
    model = HistGradientBoostingRegressor(loss="poisson", max_iter=300, learning_rate=0.05)
    model.fit(xtr, tr["k"] / tr["E"], sample_weight=tr["E"])
    return model.predict(xte)


def gbm_rate_oof(f: pd.DataFrame, n_folds: int = 5, seed: int = 0) -> pd.Series:
    """GBM en validation croisée par département (hors échantillon) : sans ça, il apprend par
    cœur les offres de chaque entreprise (« 0 offre » → 0) et ne dit rien d'utile sur elle."""
    deps = f["departement"].fillna("?").to_numpy()
    uniq = np.random.default_rng(seed).permutation(np.unique(deps))
    fold_of = {d: i % n_folds for i, d in enumerate(uniq)}
    fold = np.array([fold_of[d] for d in deps])
    out = pd.Series(np.nan, index=f.index)
    for i in range(n_folds):
        te = fold == i
        out[te] = gbm_rate(f[~te], f[te])
    return out


def split_departements(f: pd.DataFrame, seed: int = 0) -> pd.Series:
    """True = département de test (une moitié des départements, tirée au hasard)."""
    deps = sorted(f["departement"].dropna().unique())
    rng = np.random.default_rng(seed)
    test = set(rng.choice(deps, size=len(deps) // 2, replace=False))
    return f["departement"].isin(test)


def evaluate(scores: dict[str, pd.Series], label: pd.Series, k: int = 500) -> pd.DataFrame:
    """AUC et précision dans les k premiers, pour chaque score candidat (même index que label)."""
    y = label.astype(bool)
    rows = []
    for name, s in scores.items():
        s = s.reindex(y.index).fillna(s.min())
        top = y.to_numpy()[np.argsort(-s.to_numpy(), kind="stable")[:k]]
        rows.append({"score": name, "AUC": roc_auc_score(y, s), f"précision@{k}": top.mean()})
    return pd.DataFrame(rows).set_index("score")
