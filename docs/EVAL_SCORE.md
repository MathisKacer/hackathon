# Évaluation du score d'intensité (T69) — généré par `scripts/eval_score.py`

**Validation temporelle.** Les offres Adzuna sont coupées à la date médiane de publication :
les modèles ne voient que les offres d'avant, et on mesure s'ils retrouvent les entreprises qui
publient une offre data **après**. Coupure au 2026-11-13 : 7,799 offres avant, 7,834 après. Besoin caché : 253 entreprises sur 268,104 ; besoin futur : 391 sur 268,561.

L'AUC « à taille comparable » est calculée dans chaque tranche d'effectif puis moyennée : elle
retire l'avantage mécanique des grandes entreprises (qui publient plus).

## Besoin caché : entreprises sans offre avant, qui en publient une après (couche orange)

| score | AUC | AUC à taille comparable | trouvées dans le top 200 |
|---|---|---|---|
| v0 : moyenne du secteur (NAF) | 0.802 | 0.825 | 1.0 |
| v0 : + offres de l'entreprise (D13, actuel) | 0.744 | 0.808 | 1.0 |
| v1 : covariables seules (a priori) | 0.836 | 0.831 | 12.0 |
| v1 : covariables + offres, bayésien classique | 0.811 | 0.818 | 4.0 |
| v1 : covariables + offres, à sens unique (production) | 0.836 | 0.831 | 12.0 |
| note LLM seule (secteur × taille) | 0.787 | 0.699 | 9.0 |
| v1 sans NAF ni note LLM (témoin) | 0.829 | 0.8 | 8.0 |
| v1 : note LLM à la place du NAF | 0.849 | 0.833 | 8.0 |
| v1 : NAF + note LLM | 0.833 | 0.831 | 11.0 |
| v0 : volume attendu (× effectif) | 0.919 | 0.838 | 14.0 |
| v1 : volume attendu (× effectif), sens unique | 0.901 | 0.844 | 29.0 |
| GBM (arbres boostés) : volume attendu, hors échantillon | 0.885 | 0.799 | 15.0 |
| témoin : effectif seul | 0.842 | 0.571 | 20.0 |
| score affiché, poids intensité 2 / besoin 4 (défaut) | 0.921 | 0.843 | 16.0 |
| score affiché, poids intensité 3 / besoin 3 | 0.914 | 0.841 | 15.0 |
| score affiché, poids intensité 1 / besoin 5 | 0.925 | 0.844 | 19.0 |
| score affiché, poids intensité 0 / besoin 1 | 0.926 | 0.843 | 29.0 |
| score affiché, poids intensité 1 / besoin 0 | 0.852 | 0.833 | 8.0 |
| score affiché 3 / 3, échelle plafonnée à 99.5% | 0.913 | 0.837 | 13.0 |
| score affiché 2 / 4, échelle plafonnée à 99.5% | 0.92 | 0.838 | 13.0 |
| score affiché 3 / 3, échelle plafonnée à 100.0% | 0.918 | 0.842 | 17.0 |
| score affiché 2 / 4, échelle plafonnée à 100.0% | 0.923 | 0.844 | 18.0 |
| score affiché 3 / 3, ancienne échelle (rangs centiles) | 0.899 | 0.834 | 14.0 |

## Besoin futur : toutes les entreprises de la zone collectée

| score | AUC | AUC à taille comparable | trouvées dans le top 200 |
|---|---|---|---|
| v0 : moyenne du secteur (NAF) | 0.833 | 0.849 | 5.0 |
| v0 : + offres de l'entreprise (D13, actuel) | 0.817 | 0.86 | 73.0 |
| v1 : covariables seules (a priori) | 0.867 | 0.86 | 18.0 |
| v1 : covariables + offres, bayésien classique | 0.874 | 0.874 | 69.0 |
| v1 : covariables + offres, à sens unique (production) | 0.888 | 0.88 | 65.0 |
| note LLM seule (secteur × taille) | 0.804 | 0.719 | 24.0 |
| v1 sans NAF ni note LLM (témoin) | 0.884 | 0.861 | 65.0 |
| v1 : note LLM à la place du NAF | 0.898 | 0.882 | 59.0 |
| v1 : NAF + note LLM | 0.886 | 0.88 | 65.0 |
| v0 : volume attendu (× effectif) | 0.944 | 0.881 | 86.0 |
| v1 : volume attendu (× effectif), sens unique | 0.935 | 0.89 | 78.0 |
| GBM (arbres boostés) : volume attendu, hors échantillon | 0.899 | 0.813 | 29.0 |
| témoin : effectif seul | 0.85 | 0.579 | 30.0 |
| score affiché, poids intensité 2 / besoin 4 (défaut) | 0.948 | 0.889 | 72.0 |
| score affiché, poids intensité 3 / besoin 3 | 0.943 | 0.888 | 68.0 |
| score affiché, poids intensité 1 / besoin 5 | 0.95 | 0.889 | 71.0 |
| score affiché, poids intensité 0 / besoin 1 | 0.951 | 0.888 | 76.0 |
| score affiché, poids intensité 1 / besoin 0 | 0.9 | 0.882 | 61.0 |
| score affiché 3 / 3, échelle plafonnée à 99.5% | 0.942 | 0.884 | 41.0 |
| score affiché 2 / 4, échelle plafonnée à 99.5% | 0.947 | 0.885 | 41.0 |
| score affiché 3 / 3, échelle plafonnée à 100.0% | 0.945 | 0.889 | 76.0 |
| score affiché 2 / 4, échelle plafonnée à 100.0% | 0.949 | 0.89 | 76.0 |
| score affiché 3 / 3, ancienne échelle (rangs centiles) | 0.932 | 0.883 | 74.0 |

## Coefficients du modèle v1 (Poisson, offset log exposition ; φ = 23.44), hors NAF

« effet × » : multiplicateur de l'intensité attendue pour +1 sur la variable. Intervalles à
95 % avec **erreurs-types robustes (sandwich)** : celles de Poisson seraient trop étroites
(surdispersion).

|  | coef | IC bas | IC haut | effet × |
|---|---|---|---|---|
| const | -7.065 | -8.369 | -5.761 | 0.0 |
| log_effectif | 0.011 | -0.183 | 0.205 | 1.01 |
| log_n_etab | -0.423 | -0.61 | -0.236 | 0.66 |
| log_age | 0.126 | -0.138 | 0.39 | 1.13 |
| jeune_moins_5_ans | -0.415 | -1.167 | 0.338 | 0.66 |
| log_modif_capital | 0.492 | 0.208 | 0.776 | 1.64 |
| augmentation_capital | 0.063 | -0.467 | 0.593 | 1.07 |
| log_densite_data | 0.323 | 0.234 | 0.411 | 1.38 |
| ess | -0.315 | -0.93 | 0.3 | 0.73 |
| cat_ETI | 0.565 | 0.163 | 0.967 | 1.76 |
| cat_GE | 0.595 | 0.151 | 1.039 | 1.81 |

## Note LLM secteur × taille (T77)

Note 0–3 donnée par un LLM (Qwen 2.5 14B, consigne v3) pour chaque NAF × taille d'établissement, **sans voir aucune offre** (méthode : `docs/PISTE_DOMAINES_LLM.md`). Entrée en indicatrices cumulées (note ≥ 1, ≥ 2, ≥ 3) : « effet × » de chaque marche.

|  | coef | IC bas | IC haut | effet × |
|---|---|---|---|---|
| llm_ge1 | 1.217 | 0.807 | 1.627 | 3.38 |
| llm_ge2 | 0.296 | -0.251 | 0.843 | 1.34 |
| llm_ge3 | 1.62 | 1.173 | 2.068 | 5.05 |

Source de la note (entreprises) : naf 100.0% (division / taille = repli pour les NAF non notés).

Écarts d'AUC par bootstrap apparié (300 tirages, IC à 90 %, mesurés le 28/11) : note LLM à la place du NAF − production v1 = +0,013 [−0,010 ; +0,038] (besoin caché), +0,009 [−0,005 ; +0,025] (besoin futur) ; note LLM − témoin sans secteur = +0,025 [+0,012 ; +0,037] et +0,017 [+0,008 ; +0,025] ; NAF − témoin = +0,010 [−0,016 ; +0,036] et +0,006 [−0,012 ; +0,024]. **La note LLM apporte une information sectorielle significative, les ~60 indicatrices NAF non** ; l'écart LLM − NAF est positif mais dans le bruit. Choix (D45) : la note LLM remplace le NAF en production.

## Hypothèses du modèle : vérification (modèle de production, toutes les offres)

| Hypothèse | Mesure | Verdict |
|---|---|---|
| Offres indépendantes (pas de doublons) | 11.7% de doublons bruts (même entreprise, même titre) | corrigé : comptés une fois |
| Exposition ∝ effectif (élasticité 1) | coef. log effectif = -0.222 (IC -0.384 ; -0.06) | écart faible, absorbé par la covariable |
| Surdispersion bien modélisée | Pearson Poisson 5.43 → binomiale négative 3.77 (≈ 1 attendu) | voir ci-dessous |
| φ constant selon la taille | φ par tranche d'effectif : {'0–20': 403.426, '20–50': 349.401, '50–250': 60.616, '250–1000': 18.767, '1000–inf': 12.09} | non → φ estimé par tranche |
| Nombre de zéros | 267,851 observés, 267,841 attendus | ✅ |
| Calibration (observé / prédit par décile) | [0.39, 1.02, 0.77, 2.05, 0.97, 1.55, 0.88, 1.27, 1.17, 0.98] | haut de distribution ✅ |
| Erreurs-types | sandwich (HC0) | ✅ |

Non testables ici (à assumer) : probabilité de détection identique pour toutes les entreprises
(Adzuna ne voit pas les sites carrières ni Welcome to the Jungle), échantillon Île-de-France =
offres les plus récentes, indépendance entre filiales d'un même groupe (L7), erreurs de
rapprochement et de classification sur k (L6, L9, L25), incertitude sur β et φ non propagée
(bayésien empirique « plug-in », négligeable avec 268,561 entreprises).

## Pourquoi pas l'étiquette « recruteur d'alternants data » de La bonne alternance ?

Elle est entièrement déterminée par le code NAF (575 codes NAF, aucun mixte) : elle ne mesure
que la capacité à reproduire la correspondance NAF → métier de La bonne alternance, et
avantage mécaniquement un modèle « secteur seul ».
