# Modèle de réponse — démonstrateur (T35/T36, D6)

> ⚠️ **Réponses SIMULÉES** sur des entreprises **réelles**. Ce rapport montre que la chaîne
> « données → modèle → probabilité » fonctionne et retrouve une vérité connue ; il ne dit rien
> du comportement réel des entreprises. Fichier régénéré par `scripts/build_response.py`.

## Simulation

- 3,000 étudiants simulés, 45,000 candidatures spontanées vers
  38,144 établissements réels (score T30, positions SIRENE).
- Règle (hypothèses de l'équipe) : `radar/response/params.yaml` ; effet entreprise non observé
  σ = 0.5.
- Taux de réponse positive simulé : 18.0%.

## Résultats (étudiants jamais vus à l'entraînement)

| Indicateur | Valeur |
|---|---|
| AUC | **0.654** |
| AUC de la vraie règle (plafond) | 0.708 |
| Score de Brier | 0.1400 |
| Paramètres retrouvés (vrai atténué dans l'IC 95 %) | **7 / 7** |

L'écart d'AUC au plafond vient de l'effet propre à chaque entreprise, que le modèle
n'observe pas. Ce même effet atténue les coefficients d'une logistique d'un facteur
≈ 0.959 (non-collapsibilité du logit) : on compare donc aux
vrais coefficients atténués.

### Paramètres retrouvés vs vrais

| variable | vrai | vrai_attenue | estime | ic95_bas | ic95_haut | vrai_attenue_dans_ic |
| --- | --- | --- | --- | --- | --- | --- |
| const | -2.3 | -2.207 | -2.048 | -2.255 | -1.84 | True |
| c_intensite | 1.4 | 1.343 | 1.166 | 0.846 | 1.486 | True |
| c_embauche | 0.5 | 0.48 | 0.646 | 0.321 | 0.971 | True |
| log10_effectif | -0.45 | -0.432 | -0.503 | -0.63 | -0.377 | True |
| distance_10km | -0.15 | -0.144 | -0.154 | -0.185 | -0.123 | True |
| alternance | 0.35 | 0.336 | 0.327 | 0.271 | 0.384 | True |
| a_offre_domaine | 0.4 | 0.384 | 0.378 | 0.237 | 0.518 | True |

### Calibration (déciles de probabilité prédite)

| decile | predit | observe | n |
| --- | --- | --- | --- |
| 0 | 0.0696 | 0.056 | 1125 |
| 1 | 0.101 | 0.0818 | 1125 |
| 2 | 0.1236 | 0.1173 | 1125 |
| 3 | 0.1441 | 0.1556 | 1125 |
| 4 | 0.1642 | 0.152 | 1125 |
| 5 | 0.1862 | 0.1796 | 1125 |
| 6 | 0.2102 | 0.2062 | 1125 |
| 7 | 0.2365 | 0.2471 | 1125 |
| 8 | 0.266 | 0.2693 | 1125 |
| 9 | 0.3202 | 0.3129 | 1125 |

## Pour le pitch

« Les entreprises et leurs besoins sont réels ; les réponses sont simulées faute de données
ouvertes. Le modèle retrouve la règle cachée et il est bien calibré : la chaîne est prête à être
réentraînée sur les vrais retours des utilisateurs (historique des recherches, D14). »
