# Modèle de réponse — démonstrateur (T35/T36, D6)

> ⚠️ **Réponses SIMULÉES** sur des entreprises **réelles**. Ce rapport montre que la chaîne
> « données → modèle → probabilité » fonctionne et retrouve une vérité connue ; il ne dit rien
> du comportement réel des entreprises. Fichier régénéré par `scripts/build_response.py`.

## Simulation

- 3,000 étudiants simulés, 45,000 candidatures spontanées vers
  38,256 établissements réels (score T30, positions SIRENE).
- Règle (hypothèses de l'équipe) : `radar/response/params.yaml` ; effet entreprise non observé
  σ = 0.5.
- Taux de réponse positive simulé : 17.8%.

## Résultats (étudiants jamais vus à l'entraînement)

| Indicateur | Valeur |
|---|---|
| AUC | **0.642** |
| AUC de la vraie règle (plafond) | 0.686 |
| Score de Brier | 0.1399 |
| Paramètres retrouvés (vrai atténué dans l'IC 95 %) | **7 / 7** |

L'écart d'AUC au plafond vient de l'effet propre à chaque entreprise, que le modèle
n'observe pas. Ce même effet atténue les coefficients d'une logistique d'un facteur
≈ 0.959 (non-collapsibilité du logit) : on compare donc aux
vrais coefficients atténués.

### Paramètres retrouvés vs vrais

| variable | vrai | vrai_attenue | estime | ic95_bas | ic95_haut | vrai_attenue_dans_ic |
| --- | --- | --- | --- | --- | --- | --- |
| const | -2.3 | -2.207 | -2.047 | -2.255 | -1.839 | True |
| c_intensite | 1.4 | 1.343 | 1.11 | 0.791 | 1.429 | True |
| c_embauche | 0.5 | 0.48 | 0.778 | 0.455 | 1.1 | True |
| log10_effectif | -0.45 | -0.432 | -0.544 | -0.67 | -0.419 | True |
| distance_10km | -0.15 | -0.144 | -0.159 | -0.191 | -0.128 | True |
| alternance | 0.35 | 0.336 | 0.301 | 0.244 | 0.359 | True |
| a_offre_domaine | 0.4 | 0.384 | 0.479 | 0.342 | 0.615 | True |

### Calibration (déciles de probabilité prédite)

| decile | predit | observe | n |
| --- | --- | --- | --- |
| 0 | 0.0638 | 0.0693 | 1125 |
| 1 | 0.0955 | 0.0969 | 1125 |
| 2 | 0.1178 | 0.1147 | 1125 |
| 3 | 0.1385 | 0.1413 | 1125 |
| 4 | 0.158 | 0.1449 | 1125 |
| 5 | 0.1816 | 0.1849 | 1125 |
| 6 | 0.2063 | 0.2178 | 1125 |
| 7 | 0.2329 | 0.2302 | 1125 |
| 8 | 0.2613 | 0.2409 | 1125 |
| 9 | 0.3209 | 0.3191 | 1125 |

## Pour le pitch

« Les entreprises et leurs besoins sont réels ; les réponses sont simulées faute de données
ouvertes. Le modèle retrouve la règle cachée et il est bien calibré : la chaîne est prête à être
réentraînée sur les vrais retours des utilisateurs (historique des recherches, D14). »
