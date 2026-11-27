# Modèle de réponse — démonstrateur (T35/T36, D6)

> ⚠️ **Réponses SIMULÉES** sur des entreprises **réelles**. Ce rapport montre que la chaîne
> « données → modèle → probabilité » fonctionne et retrouve une vérité connue ; il ne dit rien
> du comportement réel des entreprises. Fichier régénéré par `scripts/build_response.py`.

## Simulation

- 3,000 étudiants simulés, 45,000 candidatures spontanées vers
  38,416 établissements réels (score T30, positions SIRENE).
- Règle (hypothèses de l'équipe) : `radar/response/params.yaml` ; effet entreprise non observé
  σ = 0.5.
- Taux de réponse positive simulé : 18.9%.

## Résultats (étudiants jamais vus à l'entraînement)

| Indicateur | Valeur |
|---|---|
| AUC | **0.624** |
| AUC de la vraie règle (plafond) | 0.687 |
| Score de Brier | 0.1494 |
| Paramètres retrouvés (vrai atténué dans l'IC 95 %) | **5 / 7** |

L'écart d'AUC au plafond vient de l'effet propre à chaque entreprise, que le modèle
n'observe pas. Ce même effet atténue les coefficients d'une logistique d'un facteur
≈ 0.959 (non-collapsibilité du logit) : on compare donc aux
vrais coefficients atténués.

### Paramètres retrouvés vs vrais

| variable | vrai | vrai_attenue | estime | ic95_bas | ic95_haut | vrai_attenue_dans_ic |
| --- | --- | --- | --- | --- | --- | --- |
| const | -2.3 | -2.207 | -2.16 | -2.373 | -1.947 | True |
| c_intensite | 1.4 | 1.343 | 1.056 | 0.53 | 1.582 | True |
| c_embauche | 0.5 | 0.48 | 0.83 | 0.287 | 1.373 | True |
| log10_effectif | -0.45 | -0.432 | -0.48 | -0.605 | -0.356 | True |
| distance_10km | -0.15 | -0.144 | -0.142 | -0.176 | -0.107 | True |
| alternance | 0.35 | 0.336 | 0.276 | 0.22 | 0.332 | False |
| a_offre_domaine | 0.4 | 0.384 | 0.524 | 0.392 | 0.655 | False |

### Calibration (déciles de probabilité prédite)

| decile | predit | observe | n |
| --- | --- | --- | --- |
| 0 | 0.0674 | 0.0871 | 1125 |
| 1 | 0.1046 | 0.1093 | 1125 |
| 2 | 0.1326 | 0.1262 | 1125 |
| 3 | 0.1562 | 0.1609 | 1125 |
| 4 | 0.1774 | 0.2044 | 1125 |
| 5 | 0.1974 | 0.1876 | 1125 |
| 6 | 0.217 | 0.2258 | 1125 |
| 7 | 0.2384 | 0.2347 | 1125 |
| 8 | 0.2644 | 0.2382 | 1125 |
| 9 | 0.3198 | 0.3253 | 1125 |

## Pour le pitch

« Les entreprises et leurs besoins sont réels ; les réponses sont simulées faute de données
ouvertes. Le modèle retrouve la règle cachée et il est bien calibré : la chaîne est prête à être
réentraînée sur les vrais retours des utilisateurs (historique des recherches, D14). »
