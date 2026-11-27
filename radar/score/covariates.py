"""T69 — Score v1 : bayésien empirique AVEC covariables (régression binomiale négative).

v0 (D13) : λ_i ~ Gamma(α_s, β_s) avec un a priori par secteur NAF seulement.
v1       : λ_i ~ Gamma(shape = 1/φ, moyenne μ_i),  log μ_i = x_i·β
           k_i | λ_i ~ Poisson(λ_i · E_i)   ⇒   k_i ~ BinNeg(μ_i E_i, φ)
           a posteriori : λ_i | k_i ~ Gamma(1/φ + k_i, 1/(φ μ_i) + E_i)

x_i : division NAF (indicatrices), log effectif, log nb d'établissements, âge, modifications de
capital BODACC (levées de fonds), densité d'entreprises data à proximité, catégorie, ESS, mission.
β : régression de Poisson avec offset log E_i (pseudo-MV : convergent même en cas de
surdispersion), erreurs-types robustes (sandwich) ; φ : maximum de vraisemblance binomiale
négative à β fixé, par tranche d'effectif. Offres en double (même entreprise, même titre)
comptées une fois (voir `build._dedupe_postings`).
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
from scipy.optimize import minimize_scalar
from scipy.special import gammaln
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
]
# « société à mission » retirée : 0,36 % des entreprises, aucune avec une offre data →
# séparation complète (coefficient → −∞, elles ne seraient jamais recommandées).


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


SIZE_BANDS = [0, 20, 50, 250, 1000, np.inf]  # tranches d'effectif pour φ (dispersion)


def _nb_loglik(y: np.ndarray, m: np.ndarray, phi: float) -> float:
    """Log-vraisemblance binomiale négative (NB2 : Var = m + φ m²)."""
    r = 1.0 / phi
    return float(
        np.sum(
            gammaln(y + r) - gammaln(r) - gammaln(y + 1)
            + r * np.log(r / (r + m)) + y * np.log(m / (r + m))
        )
    )  # fmt: skip


def mle_phi(y: np.ndarray, m: np.ndarray) -> float:
    """φ par maximum de vraisemblance, à moyennes m fixées (pseudo-MV, unidimensionnel)."""
    if (y > 0).sum() < 5:
        return 1.0
    res = minimize_scalar(
        lambda t: -_nb_loglik(y, m, float(np.exp(t))), bounds=(-6, 6), method="bounded"
    )
    return float(np.exp(res.x))


class CovariateModel:
    one_sided: bool = True  # a posteriori à sens unique (D33), voir posterior()

    """Régression de Poisson (offset log E), erreurs-types **robustes** (sandwich, la variance
    réelle dépasse celle de Poisson) ; dispersion φ par maximum de vraisemblance binomiale
    négative, **par tranche d'effectif** (elle n'est pas constante, D33) → a priori Gamma."""

    def fit(self, f: pd.DataFrame) -> CovariateModel:
        fit_rows = f[f["E"] > 0]
        x, self.divisions = design(fit_rows)
        # Colonnes constantes (ex. aucune société à mission dans l'échantillon) : matrice
        # singulière pour IRLS → retirées ; coefficient 0 à la prédiction (reindex/fillna).
        x = x.loc[:, (x.std() > 0) | (x.columns == "const")]
        offset = np.log(fit_rows["E"].to_numpy(float))
        y = fit_rows["k"].to_numpy(float)
        glm = sm.GLM(y, x, family=sm.families.Poisson(), offset=offset)
        # Pseudo-MV de Poisson : β convergent même si la loi n'est pas Poisson ; les erreurs-
        # types de Poisson, elles, seraient fausses (surdispersion) → sandwich (HC0).
        self.res = glm.fit(maxiter=100, cov_type="HC0")
        mu = np.asarray(self.res.predict(x, offset=offset), dtype=float)
        self.phi = mle_phi(y, mu)
        band = pd.cut(fit_rows["effectif_entreprise"], SIZE_BANDS, labels=False).to_numpy()
        self.phi_by_band = {
            int(b): mle_phi(y[band == b], mu[band == b]) for b in np.unique(band[~np.isnan(band)])
        }
        return self

    def phi_of(self, f: pd.DataFrame) -> np.ndarray:
        band = pd.cut(f["effectif_entreprise"], SIZE_BANDS, labels=False)
        return band.map(self.phi_by_band).fillna(self.phi).to_numpy(float)

    def prior_mean(self, f: pd.DataFrame) -> np.ndarray:
        """μ_i : offres du domaine attendues pour 100 salariés, d'après les covariables."""
        x, _ = design(f, self.divisions)
        return np.exp(x.to_numpy(float) @ self.res.params.reindex(x.columns).fillna(0).to_numpy())

    def posterior(self, f: pd.DataFrame) -> pd.DataFrame:
        mu = self.prior_mean(f)
        phi = self.phi_of(f)
        a = 1 / phi + f["k"].to_numpy(float)
        b = 1 / (phi * mu) + f["E"].to_numpy(float)
        q = (1 - CI_LEVEL) / 2
        post = a / b
        if self.one_sided:
            # Une offre observée fait monter l'entreprise ; l'absence d'offre ne la fait pas
            # descendre sous son a priori : la collecte ne voit qu'une partie des offres
            # (Adzuna, 60 jours), « 0 offre » n'est pas une preuve d'absence de besoin.
            post = np.maximum(post, mu)
        return pd.DataFrame(
            {
                "prior_moyenne": mu,
                "intensite_post": post,
                "intensite_ic_bas": stats.gamma.ppf(q, a, scale=1 / b),
                "intensite_ic_haut": stats.gamma.ppf(1 - q, a, scale=1 / b),
            },
            index=f.index,
        )

    def diagnostics(self, f: pd.DataFrame) -> dict:
        """Vérification des hypothèses sur la zone collectée (pour EVAL_SCORE.md)."""
        z = f[f["E"] > 0]
        y = z["k"].to_numpy(float)
        m = self.prior_mean(z) * z["E"].to_numpy(float)
        phi = self.phi_of(z)
        r = 1 / phi
        pearson_nb = float(
            np.sum((y - m) ** 2 / (m + phi * m**2)) / (len(y) - len(self.res.params))
        )
        pearson_p = float(np.sum((y - m) ** 2 / m) / (len(y) - len(self.res.params)))
        dec = pd.qcut(pd.Series(m).rank(method="first"), 10, labels=False).to_numpy()
        calib = [round(float(y[dec == d].sum() / m[dec == d].sum()), 2) for d in range(10)]
        ci = self.res.conf_int()
        return {
            "n": int(len(y)),
            "n_positifs": int((y > 0).sum()),
            "phi_global": round(self.phi, 3),
            "phi_par_tranche": {
                f"{SIZE_BANDS[b]}–{SIZE_BANDS[b + 1]}": round(v, 3)
                for b, v in self.phi_by_band.items()
            },
            "pearson_poisson": round(pearson_p, 2),
            "pearson_binneg": round(pearson_nb, 2),
            "zeros_observes": int((y == 0).sum()),
            "zeros_attendus": round(float(np.sum((r / (r + m)) ** r)), 0),
            "calibration_deciles": calib,
            "elasticite_effectif": (
                round(float(self.res.params["log_effectif"]), 3),
                round(float(ci.loc["log_effectif", 0]), 3),
                round(float(ci.loc["log_effectif", 1]), 3),
            ),
        }


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
