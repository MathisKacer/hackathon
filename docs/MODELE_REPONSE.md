# Modèle de réponse — démonstrateur (T35/T36, D6)

> ⚠️ **Réponses SIMULÉES** sur des entreprises **réelles**. Ce rapport montre que la chaîne
> « données → modèle → probabilité » fonctionne et retrouve une vérité connue ; il ne dit rien
> du comportement réel des entreprises. Fichier régénéré par `scripts/build_response.py`.

## Simulation

- 3,000 étudiants simulés, 45,000 candidatures spontanées vers
  38,591 établissements réels (score T30, positions SIRENE).
- Règle (hypothèses de l'équipe) : `radar/response/params.yaml` ; effet entreprise non observé
  σ = 0.5.
- Taux de réponse positive simulé : 19.1%.

## Résultats (étudiants jamais vus à l'entraînement)

| Indicateur | Valeur |
|---|---|
| AUC | **0.626** |
| AUC de la vraie règle (plafond) | 0.686 |
| Score de Brier | 0.1486 |
| Paramètres retrouvés (vrai atténué dans l'IC 95 %) | **7 / 7** |

L'écart d'AUC au plafond vient de l'effet propre à chaque entreprise, que le modèle
n'observe pas. Ce même effet atténue les coefficients d'une logistique d'un facteur
≈ 0.959 (non-collapsibilité du logit) : on compare donc aux
vrais coefficients atténués.

### Paramètres retrouvés vs vrais

| variable | vrai | vrai_attenue | estime | ic95_bas | ic95_haut | vrai_attenue_dans_ic |
| --- | --- | --- | --- | --- | --- | --- |
| const | -2.3 | -2.207 | -2.264 | -2.482 | -2.046 | True |
| c_intensite | 1.4 | 1.343 | 1.443 | 0.968 | 1.918 | True |
| c_embauche | 0.5 | 0.48 | 0.298 | -0.187 | 0.782 | True |
| log10_effectif | -0.45 | -0.432 | -0.337 | -0.457 | -0.218 | True |
| distance_10km | -0.15 | -0.144 | -0.138 | -0.175 | -0.101 | True |
| alternance | 0.35 | 0.336 | 0.309 | 0.254 | 0.365 | True |
| a_offre_domaine | 0.4 | 0.384 | 0.367 | 0.23 | 0.503 | True |

### Calibration (déciles de probabilité prédite)

| decile | predit | observe | n |
| --- | --- | --- | --- |
| 0 | 0.0756 | 0.0764 | 1125 |
| 1 | 0.1178 | 0.1156 | 1125 |
| 2 | 0.1461 | 0.1413 | 1125 |
| 3 | 0.1681 | 0.1564 | 1125 |
| 4 | 0.1871 | 0.1671 | 1125 |
| 5 | 0.2043 | 0.2027 | 1125 |
| 6 | 0.221 | 0.2284 | 1125 |
| 7 | 0.239 | 0.2284 | 1125 |
| 8 | 0.2603 | 0.2596 | 1125 |
| 9 | 0.308 | 0.3129 | 1125 |

## Pour le pitch

« Les entreprises et leurs besoins sont réels ; les réponses sont simulées faute de données
ouvertes. Le modèle retrouve la règle cachée et il est bien calibré : la chaîne est prête à être
réentraînée sur les vrais retours des utilisateurs (historique des recherches, D14). »
