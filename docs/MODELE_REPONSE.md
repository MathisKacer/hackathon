# Modèle de réponse — démonstrateur (T35/T36, D6)

> ⚠️ **Réponses SIMULÉES** sur des entreprises **réelles**. Ce rapport montre que la chaîne
> « données → modèle → probabilité » fonctionne et retrouve une vérité connue ; il ne dit rien
> du comportement réel des entreprises. Fichier régénéré par `scripts/build_response.py`.

## Simulation

- 3,000 étudiants simulés, 45,000 candidatures spontanées vers
  38,457 établissements réels (score T30, positions SIRENE).
- Règle (hypothèses de l'équipe) : `radar/response/params.yaml` ; effet entreprise non observé
  σ = 0.5.
- Taux de réponse positive simulé : 18.8%.

## Résultats (étudiants jamais vus à l'entraînement)

| Indicateur | Valeur |
|---|---|
| AUC | **0.637** |
| AUC de la vraie règle (plafond) | 0.694 |
| Score de Brier | 0.1463 |
| Paramètres retrouvés (vrai atténué dans l'IC 95 %) | **7 / 7** |

L'écart d'AUC au plafond vient de l'effet propre à chaque entreprise, que le modèle
n'observe pas. Ce même effet atténue les coefficients d'une logistique d'un facteur
≈ 0.959 (non-collapsibilité du logit) : on compare donc aux
vrais coefficients atténués.

### Paramètres retrouvés vs vrais

| variable | vrai | vrai_attenue | estime | ic95_bas | ic95_haut | vrai_attenue_dans_ic |
| --- | --- | --- | --- | --- | --- | --- |
| const | -2.3 | -2.207 | -2.158 | -2.366 | -1.949 | True |
| c_intensite | 1.4 | 1.343 | 1.292 | 0.752 | 1.832 | True |
| c_embauche | 0.5 | 0.48 | 0.527 | -0.031 | 1.084 | True |
| log10_effectif | -0.45 | -0.432 | -0.445 | -0.568 | -0.322 | True |
| distance_10km | -0.15 | -0.144 | -0.147 | -0.181 | -0.113 | True |
| alternance | 0.35 | 0.336 | 0.308 | 0.252 | 0.364 | True |
| a_offre_domaine | 0.4 | 0.384 | 0.441 | 0.312 | 0.571 | True |

### Calibration (déciles de probabilité prédite)

| decile | predit | observe | n |
| --- | --- | --- | --- |
| 0 | 0.0673 | 0.0622 | 1125 |
| 1 | 0.1061 | 0.096 | 1125 |
| 2 | 0.1342 | 0.1449 | 1125 |
| 3 | 0.1572 | 0.152 | 1125 |
| 4 | 0.1781 | 0.1796 | 1125 |
| 5 | 0.1977 | 0.2027 | 1125 |
| 6 | 0.2169 | 0.2258 | 1125 |
| 7 | 0.2374 | 0.2329 | 1125 |
| 8 | 0.2624 | 0.2524 | 1125 |
| 9 | 0.3153 | 0.3173 | 1125 |

## Pour le pitch

« Les entreprises et leurs besoins sont réels ; les réponses sont simulées faute de données
ouvertes. Le modèle retrouve la règle cachée et il est bien calibré : la chaîne est prête à être
réentraînée sur les vrais retours des utilisateurs (historique des recherches, D14). »
