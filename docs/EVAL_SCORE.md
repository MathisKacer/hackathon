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
| note LLM seule (secteur × taille) | 0.812 | 0.72 | 9.0 |
| v1 sans NAF ni note LLM (témoin) | 0.819 | 0.791 | 9.0 |
| v1 : note LLM à la place du NAF | 0.843 | 0.827 | 9.0 |
| v1 : NAF + note LLM | 0.83 | 0.818 | 8.0 |
| GBM (arbres boostés), hors échantillon | 0.589 | 0.6 | 3.0 |
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
| note LLM seule (secteur × taille) | 0.826 | 0.734 | 22.0 |
| v1 sans NAF ni note LLM (témoin) | 0.871 | 0.848 | 51.0 |
| v1 : note LLM à la place du NAF | 0.887 | 0.872 | 48.0 |
| v1 : NAF + note LLM | 0.877 | 0.864 | 49.0 |
| GBM (arbres boostés), hors échantillon | 0.624 | 0.636 | 6.0 |
| v0 : volume attendu (× effectif) | 0.947 | 0.858 | 71.0 |
| v1 : volume attendu (× effectif), sens unique | 0.937 | 0.877 | 74.0 |
| témoin : effectif seul | 0.878 | 0.593 | 33.0 |

## Coefficients du modèle v1 (Poisson, offset log exposition ; φ = 28.02), hors NAF

« effet × » : multiplicateur de l'intensité attendue pour +1 sur la variable. Intervalles à
95 % avec **erreurs-types robustes (sandwich)** : celles de Poisson seraient trop étroites
(surdispersion).

|  | coef | IC bas | IC haut | effet × |
|---|---|---|---|---|
| const | -6.542 | -8.118 | -4.967 | 0.0 |
| log_effectif | -0.059 | -0.272 | 0.154 | 0.94 |
| log_n_etab | -0.272 | -0.475 | -0.069 | 0.76 |
| log_age | 0.138 | -0.193 | 0.469 | 1.15 |
| jeune_moins_5_ans | -0.142 | -1.009 | 0.725 | 0.87 |
| log_modif_capital | 0.377 | 0.045 | 0.708 | 1.46 |
| augmentation_capital | -0.046 | -0.642 | 0.549 | 0.96 |
| log_densite_data | 0.334 | 0.231 | 0.436 | 1.4 |
| ess | -0.857 | -1.695 | -0.02 | 0.42 |
| cat_ETI | 0.536 | 0.002 | 1.07 | 1.71 |
| cat_GE | 0.671 | 0.121 | 1.221 | 1.96 |

## Note LLM secteur × taille (T77)

Note 0–3 donnée par un LLM (Qwen 2.5 14B, consigne v3) pour chaque NAF × taille d'établissement, **sans voir aucune offre** (méthode : `docs/PISTE_DOMAINES_LLM.md`). Entrée en indicatrices cumulées (note ≥ 1, ≥ 2, ≥ 3) : « effet × » de chaque marche.

|  | coef | IC bas | IC haut | effet × |
|---|---|---|---|---|
| llm_ge1 | 1.354 | 0.814 | 1.894 | 3.87 |
| llm_ge2 | 0.295 | -0.345 | 0.936 | 1.34 |
| llm_ge3 | 1.388 | 0.813 | 1.963 | 4.01 |

Source de la note (entreprises) : naf 94.7%, division 5.0%, taille 0.3% (division / taille = repli pour les NAF non notés).

Écarts d'AUC par bootstrap apparié (300 tirages, IC à 90 %, mesurés le 28/11) : note LLM à la place du NAF − production v1 = +0,013 [−0,010 ; +0,038] (besoin caché), +0,009 [−0,005 ; +0,025] (besoin futur) ; note LLM − témoin sans secteur = +0,025 [+0,012 ; +0,037] et +0,017 [+0,008 ; +0,025] ; NAF − témoin = +0,010 [−0,016 ; +0,036] et +0,006 [−0,012 ; +0,024]. **La note LLM apporte une information sectorielle significative, les ~60 indicatrices NAF non** ; l'écart LLM − NAF est positif mais dans le bruit. Choix (D45) : la note LLM remplace le NAF en production.

## Hypothèses du modèle : vérification (modèle de production, toutes les offres)

| Hypothèse | Mesure | Verdict |
|---|---|---|
| Offres indépendantes (pas de doublons) | 9.7% de doublons bruts (même entreprise, même titre) | corrigé : comptés une fois |
| Exposition ∝ effectif (élasticité 1) | coef. log effectif = 0.081 (IC -0.159 ; 0.322) | écart faible, absorbé par la covariable |
| Surdispersion bien modélisée | Pearson Poisson 6.03 → binomiale négative 4.7 (≈ 1 attendu) | voir ci-dessous |
| φ constant selon la taille | φ par tranche d'effectif : {'0–20': 403.426, '20–50': 173.047, '50–250': 38.715, '250–1000': 12.719, '1000–inf': 6.237} | non → φ estimé par tranche |
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
