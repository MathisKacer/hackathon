"""Modèle de réponse démonstrateur (T35 + T36, D6) — réponses SIMULÉES sur entreprises réelles.

    uv run python scripts/build_response.py

Prérequis : scores.parquet (scripts/build_all.py). Règle de simulation : radar/response/params.yaml.
Sorties : candidatures_simulees.parquet, p_reponse.parquet, modele_reponse.json (data/processed/).
"""

import pandas as pd

from radar.config import PATHS
from radar.response import model, simulate
from radar.response.simulate import load_params

REPORT = PATHS.root / "docs" / "MODELE_REPONSE.md"


def md_table(df: pd.DataFrame) -> str:
    rows = [list(map(str, df.columns)), ["---"] * len(df.columns)]
    rows += [[str(v) for v in r] for r in df.itertuples(index=False)]
    return "\n".join("| " + " | ".join(r) + " |" for r in rows)


def write_report(cand: pd.DataFrame, r: dict) -> None:
    """Rapport pour le pitch, régénéré à chaque exécution (ne pas l'éditer à la main)."""
    par = pd.DataFrame(r["parametres"])
    cal = pd.DataFrame(r["calibration"])
    n_ok = int(par["vrai_attenue_dans_ic"].sum())
    REPORT.write_text(
        f"""# Modèle de réponse — démonstrateur (T35/T36, D6)

> ⚠️ **Réponses SIMULÉES** sur des entreprises **réelles**. Ce rapport montre que la chaîne
> « données → modèle → probabilité » fonctionne et retrouve une vérité connue ; il ne dit rien
> du comportement réel des entreprises. Fichier régénéré par `scripts/build_response.py`.

## Simulation

- {cand["profil_id"].nunique():,} étudiants simulés, {len(cand):,} candidatures spontanées vers
  {cand["siret"].nunique():,} établissements réels (score T30, positions SIRENE).
- Règle (hypothèses de l'équipe) : `radar/response/params.yaml` ; effet entreprise non observé
  σ = {load_params()["sigma_entreprise"]}.
- Taux de réponse positive simulé : {cand["repondu"].mean():.1%}.

## Résultats (étudiants jamais vus à l'entraînement)

| Indicateur | Valeur |
|---|---|
| AUC | **{r["auc_test"]:.3f}** |
| AUC de la vraie règle (plafond) | {r["auc_regle_vraie"]:.3f} |
| Score de Brier | {r["brier_test"]:.4f} |
| Paramètres retrouvés (vrai atténué dans l'IC 95 %) | **{n_ok} / {len(par)}** |

L'écart d'AUC au plafond vient de l'effet propre à chaque entreprise, que le modèle
n'observe pas. Ce même effet atténue les coefficients d'une logistique d'un facteur
≈ {r["attenuation_theorique"]:.3f} (non-collapsibilité du logit) : on compare donc aux
vrais coefficients atténués.

### Paramètres retrouvés vs vrais

{md_table(par)}

### Calibration (déciles de probabilité prédite)

{md_table(cal)}

## Pour le pitch

« Les entreprises et leurs besoins sont réels ; les réponses sont simulées faute de données
ouvertes. Le modèle retrouve la règle cachée et il est bien calibré : la chaîne est prête à être
réentraînée sur les vrais retours des utilisateurs (historique des recherches, D14). »
""",
        encoding="utf-8",
    )


def main() -> None:
    cand = simulate.run()
    print(
        f"Simulation : {len(cand):,} candidatures de {cand['profil_id'].nunique():,} étudiants "
        f"vers {cand['siret'].nunique():,} établissements réels ; "
        f"taux de réponse positive {cand['repondu'].mean():.1%}"
    )
    r = model.run()
    print(f"\nModèle (test sur {r['n_test']:,} candidatures d'étudiants jamais vus) :")
    print(f"  AUC {r['auc_test']:.3f}  (plafond avec la vraie règle : {r['auc_regle_vraie']:.3f})")
    print(f"  Brier {r['brier_test']:.4f}")
    print(
        "\nParamètres retrouvés vs vrais (atténuation théorique "
        f"{r['attenuation_theorique']:.3f} due à l'effet entreprise non observé) :"
    )
    print(pd.DataFrame(r["parametres"]).to_string(index=False))
    print("\nCalibration (déciles de probabilité prédite) :")
    print(pd.DataFrame(r["calibration"]).to_string(index=False))
    write_report(cand, r)
    print(f"\nRapport → {REPORT.relative_to(PATHS.root)}")


if __name__ == "__main__":
    main()
