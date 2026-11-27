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
| const | -2.3 | -2.207 | -2.045 | -2.254 | -1.837 | True |
| c_intensite | 1.4 | 1.343 | 1.156 | 0.835 | 1.478 | True |
| c_embauche | 0.5 | 0.48 | 0.658 | 0.331 | 0.985 | True |
| log10_effectif | -0.45 | -0.432 | -0.506 | -0.632 | -0.379 | True |
| distance_10km | -0.15 | -0.144 | -0.154 | -0.185 | -0.123 | True |
| alternance | 0.35 | 0.336 | 0.327 | 0.271 | 0.384 | True |
| a_offre_domaine | 0.4 | 0.384 | 0.381 | 0.241 | 0.521 | True |

### Calibration (déciles de probabilité prédite)

| decile | predit | observe | n |
| --- | --- | --- | --- |
| 0 | 0.0697 | 0.056 | 1125 |
| 1 | 0.101 | 0.0827 | 1125 |
| 2 | 0.1237 | 0.1164 | 1125 |
| 3 | 0.1441 | 0.1582 | 1125 |
| 4 | 0.1641 | 0.1511 | 1125 |
| 5 | 0.1861 | 0.1778 | 1125 |
| 6 | 0.2102 | 0.2062 | 1125 |
| 7 | 0.2366 | 0.2462 | 1125 |
| 8 | 0.2661 | 0.2711 | 1125 |
| 9 | 0.3205 | 0.312 | 1125 |

## Pour le pitch

« Les entreprises et leurs besoins sont réels ; les réponses sont simulées faute de données
ouvertes. Le modèle retrouve la règle cachée et il est bien calibré : la chaîne est prête à être
réentraînée sur les vrais retours des utilisateurs (historique des recherches, D14). »
