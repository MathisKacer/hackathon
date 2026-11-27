# Évaluation du score d'intensité (T69) — généré par `scripts/eval_score.py`

**Validation temporelle.** Les offres Adzuna sont coupées à la date médiane de publication :
les modèles ne voient que les offres d'avant, et on mesure s'ils retrouvent les entreprises qui
publient une offre data **après**. Coupure au 2026-11-18 : 5,388 offres avant, 5,388 après. Besoin caché : 183 entreprises sur 149,881 ; besoin futur : 278 sur 150,197.

L'AUC « à taille comparable » est calculée dans chaque tranche d'effectif puis moyennée : elle
retire l'avantage mécanique des grandes entreprises (qui publient plus).

## Besoin caché : entreprises sans offre avant, qui en publient une après (couche orange)

| score | AUC | AUC à taille comparable | trouvées dans le top 200 |
|---|---|---|---|
| v0 : moyenne du secteur (NAF) | 0.794 | 0.804 | 3.0 |
| v0 : + offres de l'entreprise (D13, actuel) | 0.722 | 0.772 | 1.0 |
| v1 : covariables seules (a priori) | 0.838 | 0.821 | 8.0 |
| v1 : covariables + offres (a posteriori) | 0.831 | 0.817 | 4.0 |
| GBM (arbres boostés), hors échantillon | 0.555 | 0.477 | 3.0 |
| v0 : volume attendu (× effectif) | 0.924 | 0.805 | 13.0 |
| v1 : volume attendu (× effectif) | 0.927 | 0.836 | 28.0 |
| témoin : effectif seul | 0.875 | 0.589 | 18.0 |

## Besoin futur : toutes les entreprises de la zone collectée

| score | AUC | AUC à taille comparable | trouvées dans le top 200 |
|---|---|---|---|
| v0 : moyenne du secteur (NAF) | 0.819 | 0.826 | 11.0 |
| v0 : + offres de l'entreprise (D13, actuel) | 0.79 | 0.826 | 65.0 |
| v1 : covariables seules (a priori) | 0.861 | 0.843 | 12.0 |
| v1 : covariables + offres (a posteriori) | 0.868 | 0.853 | 35.0 |
| GBM (arbres boostés), hors échantillon | 0.557 | 0.478 | 5.0 |
| v0 : volume attendu (× effectif) | 0.945 | 0.853 | 71.0 |
| v1 : volume attendu (× effectif) | 0.947 | 0.873 | 64.0 |
| témoin : effectif seul | 0.878 | 0.593 | 33.0 |

## Coefficients du modèle v1 (Poisson, offset log exposition ; φ = 0.87), hors NAF

« effet × » : multiplicateur de l'intensité attendue pour +1 sur la variable.

|  | coef | IC bas | IC haut | effet × |
|---|---|---|---|---|
| const | -6.648 | -7.259 | -6.038 | 0.0 |
| log_effectif | -0.048 | -0.116 | 0.02 | 0.95 |
| log_n_etab | -0.272 | -0.349 | -0.194 | 0.76 |
| log_age | 0.135 | 0.007 | 0.262 | 1.14 |
| jeune_moins_5_ans | -0.113 | -0.699 | 0.472 | 0.89 |
| log_modif_capital | 0.384 | 0.232 | 0.535 | 1.47 |
| augmentation_capital | -0.093 | -0.386 | 0.199 | 0.91 |
| log_densite_data | 0.344 | 0.295 | 0.394 | 1.41 |
| ess | -0.272 | -0.683 | 0.138 | 0.76 |
| societe_mission | -2.677 | -21.192 | 15.838 | 0.07 |
| cat_ETI | 0.595 | 0.373 | 0.818 | 1.81 |
| cat_GE | 0.634 | 0.361 | 0.907 | 1.89 |

## Pourquoi pas l'étiquette « recruteur d'alternants data » de La bonne alternance ?

Elle est entièrement déterminée par le code NAF (575 codes NAF, aucun mixte) : elle ne mesure
que la capacité à reproduire la correspondance NAF → métier de La bonne alternance, et
avantage mécaniquement un modèle « secteur seul ».
