"""T36 — Modèle de réponse aux candidatures spontanées, entraîné sur les réponses SIMULÉES (D6).

Régression logistique (statsmodels, pour les intervalles de confiance) sur les variables de
`simulate.FEATURES`. Évaluation sur des étudiants jamais vus (découpage par étudiant) :
AUC, score de Brier, calibration par déciles, et **paramètres retrouvés vs vrais** (la règle
de simulation est connue, c'est tout l'intérêt de l'exercice).

Remarque statistique : la simulation contient un effet aléatoire par entreprise
(σ = sigma_entreprise) que le modèle n'observe pas. Les coefficients d'une logistique
« marginale » sont alors atténués vers 0 d'un facteur ≈ 1/√(1 + 0,346 σ²) (non-collapsibilité
du logit) : on compare donc aussi aux vrais coefficients atténués.

Sorties :
- data/processed/p_reponse.parquet : P(réponse) par (siret, domaine, contrat_visé) à DISTANCE
  NULLE + contributions de chaque variable (pour expliquer la fiche) ;
- data/processed/modele_reponse.json : coefficients (dont distance, que l'app applique selon
  l'adresse de l'utilisateur : logit(p) += coef_distance × distance_km / 10) et métriques.
"""

from __future__ import annotations

import json
import logging
import math

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import brier_score_loss, roc_auc_score

from radar.config import FILES, PATHS
from radar.response.simulate import FEATURES, candidate_pool, load_params
from radar.schemas import check_columns

log = logging.getLogger(__name__)

MODEL_FILE = PATHS.processed / "modele_reponse.json"
TEST_SHARE = 0.25


def split_by_student(cand: pd.DataFrame, seed: int = 0) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    students = cand["profil_id"].unique()
    test = set(rng.choice(students, size=int(len(students) * TEST_SHARE), replace=False))
    is_test = cand["profil_id"].isin(test)
    return cand[~is_test], cand[is_test]


def usable_features(df: pd.DataFrame) -> list[str]:
    """Variables non constantes. Une variable constante rend la matrice singulière (T53 :
    scores construits sans Adzuna → `c_intensite`, `c_embauche` constantes)."""
    return [f for f in FEATURES if df[f].astype(float).nunique(dropna=True) > 1]


def fit(train: pd.DataFrame):
    feats = usable_features(train)
    dropped = sorted(set(FEATURES) - set(feats))
    if dropped:
        log.warning(
            "Variables constantes écartées du modèle de réponse : %s (coefficient 0). "
            "Données incomplètes ? (ex. scores construits sans les offres Adzuna)",
            ", ".join(dropped),
        )
    x = sm.add_constant(train[feats].astype(float), has_constant="add")
    return sm.Logit(train["repondu"].astype(float), x).fit(disp=False)


def _coef(res, name: str) -> float:
    """Coefficient estimé, 0 pour une variable écartée (constante)."""
    return float(res.params.get(name, 0.0))


def predict(res, df: pd.DataFrame) -> np.ndarray:
    feats = [n for n in res.params.index if n != "const"]
    x = sm.add_constant(df[feats].astype(float), has_constant="add")
    return np.asarray(res.predict(x))


def evaluate(res, test: pd.DataFrame, params: dict) -> dict:
    p = predict(res, test)
    y = test["repondu"].astype(int).to_numpy()
    deciles = pd.qcut(p, 10, labels=False, duplicates="drop")
    calib = (
        pd.DataFrame({"decile": deciles, "predit": p, "observe": y})
        .groupby("decile")
        .agg(predit=("predit", "mean"), observe=("observe", "mean"), n=("observe", "size"))
        .round(4)
    )
    sigma = params["sigma_entreprise"]
    atten = 1 / math.sqrt(1 + 0.346 * sigma**2)
    true = {"const": params["coefficients"]["constante"]} | {
        f: params["coefficients"][f] for f in FEATURES
    }
    ci = res.conf_int()
    recovery = pd.DataFrame(
        {
            "vrai": pd.Series(true),
            "vrai_attenue": pd.Series(true) * atten,
            "estime": res.params,
            "ic95_bas": ci[0],
            "ic95_haut": ci[1],
        }
    ).round(3)
    recovery["vrai_attenue_dans_ic"] = (recovery["vrai_attenue"] >= recovery["ic95_bas"]) & (
        recovery["vrai_attenue"] <= recovery["ic95_haut"]
    )
    return {
        "n_train": int(res.nobs),
        "n_test": int(len(test)),
        "taux_reponse_test": float(y.mean()),
        "auc_test": float(roc_auc_score(y, p)),
        "auc_regle_vraie": float(roc_auc_score(y, test["p_vraie"])),  # plafond atteignable
        "brier_test": float(brier_score_loss(y, p)),
        "attenuation_theorique": atten,
        "calibration": calib.reset_index().to_dict(orient="records"),
        "parametres": recovery.reset_index(names="variable").to_dict(orient="records"),
    }


def score_all(res, pool: pd.DataFrame) -> pd.DataFrame:
    """P(réponse) de chaque établissement, à distance nulle, pour stage et alternance."""
    coef = res.params
    rows = []
    for contrat, alt in (("stage", 0.0), ("alternance", 1.0)):
        d = pool.assign(distance_10km=0.0, alternance=alt)
        out = d[["siret", "domaine"]].copy()
        out["contrat_vise"] = contrat
        lin = np.full(len(d), coef["const"])
        for f in FEATURES:
            contrib = _coef(res, f) * d[f].to_numpy(float)
            lin += contrib
            if f not in ("distance_10km",):
                out[f"contrib_{f}"] = contrib.astype(np.float32)
        out["p_reponse"] = (1 / (1 + np.exp(-lin))).astype(np.float32)
        out["donnees_simulees"] = True
        rows.append(out)
    p = pd.concat(rows, ignore_index=True)
    check_columns(p, "p_reponse_modele")
    return p


def run() -> dict:
    params = load_params()
    cand = pd.read_parquet(FILES["candidatures_simulees"])
    train, test = split_by_student(cand)
    res = fit(train)
    report = evaluate(res, test, params)

    scores = pd.read_parquet(FILES["scores"])
    ent = pd.read_parquet(FILES["entreprises"], columns=["siret", "lat", "lon"])
    p = score_all(res, candidate_pool(scores, ent))
    p.to_parquet(FILES["p_reponse"], index=False)

    model = {
        "description": "Logistique entraînée sur des réponses SIMULÉES (D6). Ne pas présenter "
        "comme une probabilité réelle.",
        "variables": FEATURES,
        "coefficients": {f: round(_coef(res, f), 5) for f in ["const", *FEATURES]},
        "variables_ecartees": sorted(set(FEATURES) - set(res.params.index)),
        "usage_distance": "logit(p) = logit(p_reponse) + coefficients['distance_10km'] × km / 10",
        "metriques": report,
    }
    MODEL_FILE.write_text(json.dumps(model, ensure_ascii=False, indent=1, default=float))
    return report
