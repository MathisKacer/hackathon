# Modèle de réponse — démonstrateur (T35/T36, D6)

> ⚠️ **Réponses SIMULÉES** sur des entreprises **réelles**. Ce rapport montre que la chaîne
> « données → modèle → probabilité » fonctionne et retrouve une vérité connue ; il ne dit rien
> du comportement réel des entreprises. Fichier régénéré par `scripts/build_response.py`.

## Simulation

- 3,000 étudiants simulés, 45,000 candidatures spontanées vers
  38,683 établissements réels (score T30, positions SIRENE).
- Règle (hypothèses de l'équipe) : `radar/response/params.yaml` ; effet entreprise non observé
  σ = 0.5.
- Taux de réponse positive simulé : 19.3%.

## Résultats (étudiants jamais vus à l'entraînement)

| Indicateur | Valeur |
|---|---|
| AUC | **0.632** |
| AUC de la vraie règle (plafond) | 0.676 |
| Score de Brier | 0.1496 |
| Paramètres retrouvés (vrai atténué dans l'IC 95 %) | **6 / 7** |

L'écart d'AUC au plafond vient de l'effet propre à chaque entreprise, que le modèle
n'observe pas. Ce même effet atténue les coefficients d'une logistique d'un facteur
≈ 0.959 (non-collapsibilité du logit) : on compare donc aux
vrais coefficients atténués.

### Paramètres retrouvés vs vrais

| variable | vrai | vrai_attenue | estime | ic95_bas | ic95_haut | vrai_attenue_dans_ic |
| --- | --- | --- | --- | --- | --- | --- |
| const | -2.3 | -2.207 | -2.152 | -2.374 | -1.93 | True |
| c_intensite | 1.4 | 1.343 | 1.589 | 1.111 | 2.067 | True |
| c_embauche | 0.5 | 0.48 | 0.135 | -0.345 | 0.616 | True |
| log10_effectif | -0.45 | -0.432 | -0.417 | -0.537 | -0.297 | True |
| distance_10km | -0.15 | -0.144 | -0.141 | -0.179 | -0.103 | True |
| alternance | 0.35 | 0.336 | 0.309 | 0.253 | 0.364 | True |
| a_offre_domaine | 0.4 | 0.384 | 0.64 | 0.512 | 0.768 | False |

### Calibration (déciles de probabilité prédite)

| decile | predit | observe | n |
| --- | --- | --- | --- |
| 0 | 0.0735 | 0.0667 | 1125 |
| 1 | 0.1137 | 0.112 | 1125 |
| 2 | 0.1426 | 0.1253 | 1125 |
| 3 | 0.1654 | 0.1831 | 1125 |
| 4 | 0.1853 | 0.1858 | 1125 |
| 5 | 0.2039 | 0.1964 | 1125 |
| 6 | 0.2214 | 0.2284 | 1125 |
| 7 | 0.2405 | 0.2356 | 1125 |
| 8 | 0.2644 | 0.2684 | 1125 |
| 9 | 0.3243 | 0.312 | 1125 |

## Pour le pitch

« Les entreprises et leurs besoins sont réels ; les réponses sont simulées faute de données
ouvertes. Le modèle retrouve la règle cachée et il est bien calibré : la chaîne est prête à être
réentraînée sur les vrais retours des utilisateurs (historique des recherches, D14). »
