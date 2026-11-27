# Évaluation du score d'intensité (T69) — généré par `scripts/eval_score.py`

**Validation temporelle.** Les offres Adzuna sont coupées à la date médiane de publication :
les modèles ne voient que les offres d'avant, et on mesure s'ils retrouvent les entreprises qui
publient une offre data **après**. Coupure au 2026-11-18 : 5,388 offres avant, 5,388 après. Besoin caché : 183 entreprises sur 149,881 ; besoin futur : 278 sur 150,197.

L'AUC « à taille comparable » est calculée dans chaque tranche d'effectif puis moyennée : elle
retire l'avantage mécanique des grandes entreprises (qui publient plus).

## Besoin caché : entreprises sans offre avant, qui en publient une après (couche orange)

| score | AUC | AUC à taille comparable | trouvées dans le top 200 |
|---|---|---|---|
| v0 : moyenne du secteur (NAF) | 0.793 | 0.804 | 3.0 |
| v0 : + offres de l'entreprise (D13, actuel) | 0.733 | 0.779 | 1.0 |
| v1 : covariables seules (a priori) | 0.83 | 0.817 | 8.0 |
| v1 : covariables + offres, bayésien classique | 0.809 | 0.798 | 1.0 |
| v1 : covariables + offres, à sens unique (production) | 0.83 | 0.817 | 8.0 |
| GBM (arbres boostés), hors échantillon | 0.604 | 0.562 | 1.0 |
| v0 : volume attendu (× effectif) | 0.924 | 0.81 | 14.0 |
| v1 : volume attendu (× effectif), sens unique | 0.906 | 0.831 | 29.0 |
| témoin : effectif seul | 0.875 | 0.589 | 18.0 |

## Besoin futur : toutes les entreprises de la zone collectée

| score | AUC | AUC à taille comparable | trouvées dans le top 200 |
|---|---|---|---|
| v0 : moyenne du secteur (NAF) | 0.817 | 0.825 | 11.0 |
| v0 : + offres de l'entreprise (D13, actuel) | 0.799 | 0.833 | 64.0 |
| v1 : covariables seules (a priori) | 0.856 | 0.841 | 12.0 |
| v1 : covariables + offres, bayésien classique | 0.866 | 0.854 | 60.0 |
| v1 : covariables + offres, à sens unique (production) | 0.877 | 0.863 | 54.0 |
| GBM (arbres boostés), hors échantillon | 0.606 | 0.565 | 1.0 |
| v0 : volume attendu (× effectif) | 0.947 | 0.858 | 71.0 |
| v1 : volume attendu (× effectif), sens unique | 0.937 | 0.877 | 74.0 |
| témoin : effectif seul | 0.878 | 0.593 | 33.0 |

## Coefficients du modèle v1 (Poisson, offset log exposition ; φ = 28.02), hors NAF

« effet × » : multiplicateur de l'intensité attendue pour +1 sur la variable. Intervalles à
95 % avec **erreurs-types robustes (sandwich)** : celles de Poisson seraient trop étroites
(surdispersion).

|  | coef | IC bas | IC haut | effet × |
|---|---|---|---|---|
| const | -6.542 | -8.117 | -4.966 | 0.0 |
| log_effectif | -0.059 | -0.272 | 0.154 | 0.94 |
| log_n_etab | -0.272 | -0.475 | -0.069 | 0.76 |
| log_age | 0.138 | -0.193 | 0.468 | 1.15 |
| jeune_moins_5_ans | -0.144 | -1.011 | 0.723 | 0.87 |
| log_modif_capital | 0.375 | 0.044 | 0.707 | 1.45 |
| augmentation_capital | -0.047 | -0.642 | 0.548 | 0.95 |
| log_densite_data | 0.334 | 0.231 | 0.436 | 1.4 |
| ess | -0.858 | -1.695 | -0.02 | 0.42 |
| cat_ETI | 0.536 | 0.002 | 1.07 | 1.71 |
| cat_GE | 0.671 | 0.121 | 1.221 | 1.96 |

## Hypothèses du modèle : vérification (modèle de production, toutes les offres)

| Hypothèse | Mesure | Verdict |
|---|---|---|
| Offres indépendantes (pas de doublons) | 9.7% de doublons bruts (même entreprise, même titre) | corrigé : comptés une fois |
| Exposition ∝ effectif (élasticité 1) | coef. log effectif = 0.081 (IC -0.159 ; 0.322) | écart faible, absorbé par la covariable |
| Surdispersion bien modélisée | Pearson Poisson 6.03 → binomiale négative 4.71 (≈ 1 attendu) | voir ci-dessous |
| φ constant selon la taille | φ par tranche d'effectif : {'0–20': 403.426, '20–50': 173.084, '50–250': 38.712, '250–1000': 12.726, '1000–inf': 6.237} | non → φ estimé par tranche |
| Nombre de zéros | 149,698 observés, 149,713 attendus | ✅ |
| Calibration (observé / prédit par décile) | [0.0, 0.0, 0.0, 3.21, 1.98, 2.5, 1.0, 0.42, 1.18, 0.99] | haut de distribution ✅ |
| Erreurs-types | sandwich (HC0) | ✅ |

Non testables ici (à assumer) : probabilité de détection identique pour toutes les entreprises
(Adzuna ne voit pas les sites carrières ni Welcome to the Jungle), échantillon Île-de-France =
offres les plus récentes, indépendance entre filiales d'un même groupe (L7), erreurs de
rapprochement et de classification sur k (L6, L9, L25), incertitude sur β et φ non propagée
(bayésien empirique « plug-in », négligeable avec 150,197 entreprises).

## Pourquoi pas l'étiquette « recruteur d'alternants data » de La bonne alternance ?

Elle est entièrement déterminée par le code NAF (575 codes NAF, aucun mixte) : elle ne mesure
que la capacité à reproduire la correspondance NAF → métier de La bonne alternance, et
avantage mécaniquement un modèle « secteur seul ».
