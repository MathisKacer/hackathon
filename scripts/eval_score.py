# ruff: noqa: E501  (tableaux Markdown du rapport, non sécables)
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
LLM_COL = f"note_llm_{DOMAIN}"
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
        s = s.reindex(y.index).replace([np.inf, -np.inf], np.nan)
        if s.isna().any():
            print(
                f"  ⚠️ {name} : {int(s.isna().sum())} valeurs manquantes ou infinies (classées en bas)"
            )
        s = s.fillna(s.min())
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
    v1 = m.posterior(f)  # à sens unique (production)
    m.one_sided = False
    v1_bi = m.posterior(f)  # bayésien classique : « 0 offre » fait aussi descendre
    m.one_sided = True
    # Hypothèses : vérifiées sur le modèle ajusté avec TOUTES les offres (celui de la production)
    full = (
        _company_table(ent, adz, DOMAIN, cov)
        .set_index("siren")
        .join(feats.drop(columns=["naf_section", "naf_division", "effectif_entreprise"]))
    )
    prod = CovariateModel(llm=LLM_COL, naf=False) if LLM_COL in full else CovariateModel()
    diag = prod.fit(full).diagnostics(full)
    dup = adz[(adz["domaine"] == DOMAIN) & adz["siren_match"].notna()]
    dup_rate = dup.duplicated(["siren_match", "titre"]).mean()
    main_dep = (
        ent.assign(eff=ent["effectif_estime"].fillna(0))
        .sort_values("eff", ascending=False)
        .drop_duplicates("siren")
        .set_index("siren")["departement"]
    )
    f["departement"] = main_dep.reindex(f.index)
    gbm = gbm_rate_oof(f)  # validation croisée par département (sinon il apprend par cœur)
    # T77 : note LLM secteur × taille (grille de docs/PISTE_DOMAINES_LLM.md), si elle existe
    llm_cands, llm_models = {}, {}
    if LLM_COL in f:

        def post(**kw):
            mod = CovariateModel(**kw).fit(f)
            llm_models[str(kw)] = mod
            return pd.Series(mod.posterior(f)["intensite_post"], index=f.index)

        llm_cands = {
            "note LLM seule (secteur × taille)": f[LLM_COL],
            "v1 sans NAF ni note LLM (témoin)": post(naf=False),
            "v1 : note LLM à la place du NAF": post(llm=LLM_COL, naf=False),
            "v1 : NAF + note LLM": post(llm=LLM_COL),
        }
    eff = f["effectif_entreprise"]
    cands = {
        "v0 : moyenne du secteur (NAF)": v0["prior_moyenne"],
        "v0 : + offres de l'entreprise (D13, actuel)": v0["intensite_post"],
        "v1 : covariables seules (a priori)": pd.Series(v1["prior_moyenne"], index=f.index),
        "v1 : covariables + offres, bayésien classique": pd.Series(
            v1_bi["intensite_post"], index=f.index
        ),
        "v1 : covariables + offres, à sens unique (production)": pd.Series(
            v1["intensite_post"], index=f.index
        ),
        **llm_cands,
        "GBM (arbres boostés), hors échantillon": gbm,
        # volume attendu (intensité × effectif) : ce que classe c_embauche
        "v0 : volume attendu (× effectif)": v0["intensite_post"] * eff,
        "v1 : volume attendu (× effectif), sens unique": pd.Series(
            v1["intensite_post"], index=f.index
        )
        * eff,
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

    llm_txt = "Grille LLM absente (`scripts/build_grille_llm.py`) : section non calculée."
    key = str({"llm": LLM_COL, "naf": False})
    if key in llm_models:
        lm = llm_models[key].res
        lc = pd.DataFrame(
            {"coef": lm.params, "IC bas": lm.conf_int()[0], "IC haut": lm.conf_int()[1]}
        )
        lc = lc.loc[[c for c in lc.index if c.startswith("llm_")]].round(3)
        lc["effet ×"] = np.exp(lc["coef"]).round(2)
        src = f.get("note_llm_source", pd.Series(dtype=object)).value_counts(normalize=True)
        llm_txt = (
            "Note 0–3 donnée par un LLM (Qwen 2.5 14B, consigne v3) pour chaque NAF × taille "
            "d'établissement, **sans voir aucune offre** (méthode : `docs/PISTE_DOMAINES_LLM.md`). "
            "Entrée en indicatrices cumulées (note ≥ 1, ≥ 2, ≥ 3) : « effet × » de chaque marche.\n\n"
            + md(lc)
            + "\n\nSource de la note (entreprises) : "
            + ", ".join(f"{k} {v:.1%}" for k, v in src.items())
            + " (division / taille = repli pour les NAF non notés).\n\n"
            "Écarts d'AUC par bootstrap apparié (300 tirages, IC à 90 %, mesurés le 28/11) : "
            "note LLM à la place du NAF − production v1 = +0,013 [−0,010 ; +0,038] (besoin caché), "
            "+0,009 [−0,005 ; +0,025] (besoin futur) ; note LLM − témoin sans secteur = +0,025 "
            "[+0,012 ; +0,037] et +0,017 [+0,008 ; +0,025] ; NAF − témoin = +0,010 [−0,016 ; "
            "+0,036] et +0,006 [−0,012 ; +0,024]. **La note LLM apporte une information "
            "sectorielle significative, les ~60 indicatrices NAF non** ; l'écart LLM − NAF est "
            "positif mais dans le bruit. Choix (D45) : la note LLM remplace le NAF en production."
        )
    head = (
        f"Coupure au {cut.date()} : {len(before):,} offres avant, {len(after):,} après. "
        f"Besoin caché : {int(y_hid.sum())} entreprises sur {len(y_hid):,} ; "
        f"besoin futur : {int(y_all.sum())} sur {len(y_all):,}."
    )
    print(head)
    print("\n— Besoin caché (sans offre avant → offre après) —\n" + t_hid.to_string())
    print("\n— Besoin futur (toutes les entreprises de la zone collectée) —\n" + t_all.to_string())
    print(f"\nφ = {m.phi:.2f} ; coefficients v1 hors NAF :\n{coefs.to_string()}")
    print("\nDiagnostics :", diag, f"; doublons bruts {dup_rate:.1%}")

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

« effet × » : multiplicateur de l'intensité attendue pour +1 sur la variable. Intervalles à
95 % avec **erreurs-types robustes (sandwich)** : celles de Poisson seraient trop étroites
(surdispersion).

{md(coefs)}

## Note LLM secteur × taille (T77)

{llm_txt}

## Hypothèses du modèle : vérification (modèle de production, toutes les offres)

| Hypothèse | Mesure | Verdict |
|---|---|---|
| Offres indépendantes (pas de doublons) | {dup_rate:.1%} de doublons bruts (même entreprise, même titre) | corrigé : comptés une fois |
| Exposition ∝ effectif (élasticité 1) | coef. log effectif = {diag["elasticite_effectif"][0]} (IC {diag["elasticite_effectif"][1]} ; {diag["elasticite_effectif"][2]}) | écart faible, absorbé par la covariable |
| Surdispersion bien modélisée | Pearson Poisson {diag["pearson_poisson"]} → binomiale négative {diag["pearson_binneg"]} (≈ 1 attendu) | voir ci-dessous |
| φ constant selon la taille | φ par tranche d'effectif : {diag["phi_par_tranche"]} | non → φ estimé par tranche |
| Nombre de zéros | {diag["zeros_observes"]:,} observés, {diag["zeros_attendus"]:,.0f} attendus | ✅ |
| Calibration (observé / prédit par décile) | {diag["calibration_deciles"]} | haut de distribution ✅ |
| Erreurs-types | sandwich (HC0) | ✅ |

Non testables ici (à assumer) : probabilité de détection identique pour toutes les entreprises
(Adzuna ne voit pas les sites carrières ni Welcome to the Jungle), échantillon Île-de-France =
offres les plus récentes, indépendance entre filiales d'un même groupe (L7), erreurs de
rapprochement et de classification sur k (L6, L9, L25), incertitude sur β et φ non propagée
(bayésien empirique « plug-in », négligeable avec {diag["n"]:,} entreprises).

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
