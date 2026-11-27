"""T69 — Évaluation honnête des variantes du score d'intensité (v0 D13, v1 covariables, GBM).

    uv run python scripts/eval_score.py

**Validation temporelle** (étiquette indépendante du secteur) : on coupe les offres Adzuna à la
date médiane de publication. Les modèles ne voient que les offres d'AVANT ; on mesure s'ils
retrouvent les entreprises qui publient une offre du domaine APRÈS :
  - « besoin caché » : parmi les entreprises SANS offre avant, celles qui en publient une après
    (le cas exact de la couche orange) ;
  - « besoin futur » : toutes les entreprises de la zone collectée.
Comme les grandes entreprises publient mécaniquement plus, on donne aussi l'AUC moyenne
**à taille comparable** (par tranche d'effectif).

L'étiquette « recruteur d'alternants data » de La bonne alternance n'est PAS utilisée : elle est
entièrement déterminée par le code NAF (vérifié : 575 codes, 0 exception), elle ne mesure donc
que la capacité à reproduire la correspondance NAF → métier de La bonne alternance.

Écrit docs/EVAL_SCORE.md (tableaux pour les slides).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from radar.config import FILES, PATHS
from radar.score.build import EXCLUDED_NAF_PREFIX, _company_table, load_coverage
from radar.score.covariates import CovariateModel, gbm_rate_oof
from radar.score.features import build_features
from radar.score.intensity import fit_priors, posterior

DOMAIN = "data"
REPORT = PATHS.root / "docs" / "EVAL_SCORE.md"
SIZE_BANDS = [0, 20, 50, 250, 1000, np.inf]


def auc_by_size(y: pd.Series, s: pd.Series, size: pd.Series) -> float:
    """AUC moyenne dans les tranches d'effectif (pondérée par le nombre de positifs)."""
    band = pd.cut(size, SIZE_BANDS)
    aucs, w = [], []
    for _, idx in y.groupby(band, observed=True).groups.items():
        yy = y.loc[idx]
        if 0 < yy.sum() < len(yy):
            aucs.append(roc_auc_score(yy, s.loc[idx]))
            w.append(yy.sum())
    return float(np.average(aucs, weights=w)) if aucs else float("nan")


def table(cands: dict[str, pd.Series], y: pd.Series, size: pd.Series, k: int = 200) -> pd.DataFrame:
    rows = []
    for name, s in cands.items():
        s = s.reindex(y.index).fillna(s.min())
        top = y.to_numpy()[np.argsort(-s.to_numpy(), kind="stable")[:k]]
        rows.append(
            {
                "score": name,
                "AUC": round(roc_auc_score(y, s), 3),
                "AUC à taille comparable": round(auc_by_size(y, s, size), 3),
                f"trouvées dans le top {k}": int(top.sum()),
            }
        )
    return pd.DataFrame(rows).set_index("score")


def md(df: pd.DataFrame) -> str:
    cols = [df.index.name or ""] + list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    lines += [
        "| " + " | ".join(map(str, [i, *r])) + " |"
        for i, r in zip(df.index, df.values, strict=True)
    ]
    return "\n".join(lines)


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    ent = pd.read_parquet(FILES["entreprises"])
    ent = ent[~ent["naf"].fillna("").str.startswith(EXCLUDED_NAF_PREFIX)]
    offres = pd.read_parquet(FILES["offres"])
    adz = offres[offres["source"] == "adzuna"]
    dates = pd.to_datetime(adz["date_publication"], utc=True, errors="coerce")
    cut = dates.median()
    before, after = adz[dates < cut], adz[dates >= cut]

    cov = load_coverage()
    comp = _company_table(ent, before, DOMAIN, cov).set_index("siren")  # k = offres AVANT
    k_after = _company_table(ent, after, DOMAIN, cov).set_index("siren")["k"]
    feats = build_features(ent).set_index("siren")
    f = comp.join(feats.drop(columns=["naf_section", "naf_division", "effectif_entreprise"]))

    v0 = posterior(f.reset_index(), fit_priors(f.reset_index())).set_index("siren")
    m = CovariateModel().fit(f)
    v1 = m.posterior(f)
    main_dep = (
        ent.assign(eff=ent["effectif_estime"].fillna(0))
        .sort_values("eff", ascending=False)
        .drop_duplicates("siren")
        .set_index("siren")["departement"]
    )
    f["departement"] = main_dep.reindex(f.index)
    gbm = gbm_rate_oof(f)  # validation croisée par département (sinon il apprend par cœur)
    eff = f["effectif_entreprise"]
    cands = {
        "v0 : moyenne du secteur (NAF)": v0["prior_moyenne"],
        "v0 : + offres de l'entreprise (D13, actuel)": v0["intensite_post"],
        "v1 : covariables seules (a priori)": pd.Series(v1["prior_moyenne"], index=f.index),
        "v1 : covariables + offres (a posteriori)": pd.Series(v1["intensite_post"], index=f.index),
        "GBM (arbres boostés), hors échantillon": gbm,
        # volume attendu (intensité × effectif) : ce que classe c_embauche
        "v0 : volume attendu (× effectif)": v0["intensite_post"] * eff,
        "v1 : volume attendu (× effectif)": pd.Series(v1["intensite_post"], index=f.index) * eff,
        "témoin : effectif seul": eff,
    }
    zone = f["couverture"] > 0
    y_all = (k_after.reindex(f.index).fillna(0) > 0)[zone]
    hidden = zone & (f["k"] == 0)
    y_hid = (k_after.reindex(f.index).fillna(0) > 0)[hidden]

    t_hid = table(cands, y_hid, eff[hidden])
    t_all = table(cands, y_all, eff[zone])
    coefs = pd.DataFrame(
        {"coef": m.res.params, "IC bas": m.res.conf_int()[0], "IC haut": m.res.conf_int()[1]}
    )
    coefs = coefs.drop(index=[c for c in coefs.index if c.startswith("naf_")]).round(3)
    coefs["effet ×"] = np.exp(coefs["coef"]).round(2)

    head = (
        f"Coupure au {cut.date()} : {len(before):,} offres avant, {len(after):,} après. "
        f"Besoin caché : {int(y_hid.sum())} entreprises sur {len(y_hid):,} ; "
        f"besoin futur : {int(y_all.sum())} sur {len(y_all):,}."
    )
    print(head)
    print("\n— Besoin caché (sans offre avant → offre après) —\n" + t_hid.to_string())
    print("\n— Besoin futur (toutes les entreprises de la zone collectée) —\n" + t_all.to_string())
    print(f"\nφ = {m.phi:.2f} ; coefficients v1 hors NAF :\n{coefs.to_string()}")

    REPORT.write_text(
        f"""# Évaluation du score d'intensité (T69) — généré par `scripts/eval_score.py`

**Validation temporelle.** Les offres Adzuna sont coupées à la date médiane de publication :
les modèles ne voient que les offres d'avant, et on mesure s'ils retrouvent les entreprises qui
publient une offre data **après**. {head}

L'AUC « à taille comparable » est calculée dans chaque tranche d'effectif puis moyennée : elle
retire l'avantage mécanique des grandes entreprises (qui publient plus).

## Besoin caché : entreprises sans offre avant, qui en publient une après (couche orange)

{md(t_hid)}

## Besoin futur : toutes les entreprises de la zone collectée

{md(t_all)}

## Coefficients du modèle v1 (Poisson, offset log exposition ; φ = {m.phi:.2f}), hors NAF

« effet × » : multiplicateur de l'intensité attendue pour +1 sur la variable.

{md(coefs)}

## Pourquoi pas l'étiquette « recruteur d'alternants data » de La bonne alternance ?

Elle est entièrement déterminée par le code NAF (575 codes NAF, aucun mixte) : elle ne mesure
que la capacité à reproduire la correspondance NAF → métier de La bonne alternance, et
avantage mécaniquement un modèle « secteur seul ».
""",
        encoding="utf-8",
    )
    print(f"\nRapport → {REPORT.relative_to(PATHS.root)}")


if __name__ == "__main__":
    main()
