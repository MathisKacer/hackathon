# Modèle de réponse — démonstrateur (T35/T36, D6)

> ⚠️ **Réponses SIMULÉES** sur des entreprises **réelles**. Ce rapport montre que la chaîne
> « données → modèle → probabilité » fonctionne et retrouve une vérité connue ; il ne dit rien
> du comportement réel des entreprises. Fichier régénéré par `scripts/build_response.py`.

## Simulation

- 3,000 étudiants simulés, 45,000 candidatures spontanées vers
  38,251 établissements réels (score T30, positions SIRENE).
- Règle (hypothèses de l'équipe) : `radar/response/params.yaml` ; effet entreprise non observé
  σ = 0.5.
- Taux de réponse positive simulé : 17.7%.

## Résultats (étudiants jamais vus à l'entraînement)

| Indicateur | Valeur |
|---|---|
| AUC | **0.646** |
| AUC de la vraie règle (plafond) | 0.692 |
| Score de Brier | 0.1382 |
| Paramètres retrouvés (vrai atténué dans l'IC 95 %) | **7 / 7** |

L'écart d'AUC au plafond vient de l'effet propre à chaque entreprise, que le modèle
n'observe pas. Ce même effet atténue les coefficients d'une logistique d'un facteur
≈ 0.959 (non-collapsibilité du logit) : on compare donc aux
vrais coefficients atténués.

### Paramètres retrouvés vs vrais

| variable | vrai | vrai_attenue | estime | ic95_bas | ic95_haut | vrai_attenue_dans_ic |
| --- | --- | --- | --- | --- | --- | --- |
| const | -2.3 | -2.207 | -2.196 | -2.401 | -1.991 | True |
| c_intensite | 1.4 | 1.343 | 1.213 | 0.898 | 1.528 | True |
| c_embauche | 0.5 | 0.48 | 0.601 | 0.282 | 0.92 | True |
| log10_effectif | -0.45 | -0.432 | -0.433 | -0.556 | -0.31 | True |
| distance_10km | -0.15 | -0.144 | -0.129 | -0.16 | -0.097 | True |
| alternance | 0.35 | 0.336 | 0.316 | 0.258 | 0.373 | True |
| a_offre_domaine | 0.4 | 0.384 | 0.401 | 0.262 | 0.54 | True |

### Calibration (déciles de probabilité prédite)

| decile | predit | observe | n |
| --- | --- | --- | --- |
| 0 | 0.0669 | 0.0622 | 1125 |
| 1 | 0.099 | 0.096 | 1125 |
| 2 | 0.1219 | 0.1164 | 1125 |
| 3 | 0.1427 | 0.1387 | 1125 |
| 4 | 0.1627 | 0.1564 | 1125 |
| 5 | 0.1833 | 0.1849 | 1125 |
| 6 | 0.2046 | 0.1973 | 1125 |
| 7 | 0.2275 | 0.2133 | 1125 |
| 8 | 0.2541 | 0.2631 | 1125 |
| 9 | 0.3081 | 0.312 | 1125 |

## Pour le pitch

« Les entreprises et leurs besoins sont réels ; les réponses sont simulées faute de données
ouvertes. Le modèle retrouve la règle cachée et il est bien calibré : la chaîne est prête à être
réentraînée sur les vrais retours des utilisateurs (historique des recherches, D14). »
