# Journal — Mathis

---

## 2026-11-27 — T69 suite : vérification des hypothèses du score v1

**Fait :**
- Diagnostics (désormais dans `scripts/eval_score.py` → `docs/EVAL_SCORE.md`) : surdispersion (Pearson 7,8), erreurs-types de Poisson fausses, 9,7 % de doublons, φ non constant, calibration du milieu imparfaite.
- Corrections : erreurs-types **sandwich**, **dédoublonnage** (entreprise × titre normalisé), **φ par MV binomiale négative par tranche d'effectif**, « société à mission » retirée (séparation complète), **a posteriori à sens unique**. 1 test en plus.
- Titre de D33 restauré (coupé lors d'une fusion) ; limite L28.

**Résultats / chiffres clés :**
- Besoin caché AUC 0,830 ; besoin futur 0,877 ; volume : top 200 14 → 29. Effets robustes : densité ×1,40, capital ×1,45, ETI/GE ×1,7–2,0, établissements ×0,76 ; âge non significatif.
- Modèle de réponse : 7/7.

**Points d'attention pour l'équipe :**
- Les intervalles des effets présentés avant cette correction étaient trop étroits : utiliser ceux de `docs/EVAL_SCORE.md`.

---

## 2026-11-27 — T68 (note) + T69 : score v1 avec covariables

**Fait :**
- T68 : note détaillée (NLP / LLM open source pour classer les offres) dans `TACHES.md`, limite L25.
- Audit du score : faux négatifs = réseaux géants avec 1 offre (classement correct) ; faux positifs = avocats, vétérinaires (lissage fixe, rang centile, ex æquo).
- **Erreur corrigée en cours de route** : l'étiquette « recruteur d'alternants data » de LBA est 100 % déterminée par le NAF → abandonnée ; remplacée par une **validation temporelle** (offres avant / après le 18/11).
- `radar/score/features.py` (SIRENE âge/ESS/mission, BODACC capital 128 543 annonces, densité data 3 km), `radar/score/covariates.py` (Poisson + offset, φ, a posteriori Gamma, GBM hors échantillon), `scripts/eval_score.py` → `docs/EVAL_SCORE.md`, intégration dans `build_scores` (repli v0). Décision **D33**. 4 tests (dont étude de simulation sur les effets).

**Résultats / chiffres clés :**
- Besoin caché : AUC 0,722 → **0,838** ; volume attendu : top 200 13 → **28** entreprises retrouvées. GBM : 0,56–0,63 hors échantillon (événement rare).
- Effets : capital ×1,47 ; densité data ×1,41 ; ETI/GE ×1,8 ; nb d'établissements ×0,76.
- Modèle de réponse : couverture des IC 93 % sur 8 graines (graine par défaut 5/7, malchanceuse).

**Points d'attention pour l'équipe :**
- `build_all` télécharge au premier lancement les caractéristiques (BODACC capital, SIRENE ; ~25 s), puis cache dans `data/raw/`.
- Paliers de Maxence (D32) : `c_intensite` reste un rang centile, seuils inchangés.

---

## 2026-11-27 — Fiabilité : T53, vérification de l'app (3 pages), T27

**Fait :**
- **T53** : `radar/response/model.py` écarte les variables constantes avant l'ajustement (avertissement, coefficient 0, `variables_ecartees` dans `modele_reponse.json`). Bug voisin trouvé par un test : `match_offers` plantait sur un tableau vide (toutes les offres avec SIRET source, scénario « LBA seule ») → corrigé.
- **App après la refonte en 3 pages (D30)**, vraies données Adzuna + LBA : Explorer (Rennes : 4 281 entreprises orange + 64 offres ; en alternance : 4 389 entreprises et 0 offre data publiée), Entreprises (« capgemini rennes » → 2 résultats), Mon espace : aucune exception. Le popup garde l'explication T32 (`app/carte.py`).
- **T27** : AGEPAC, KOANN, Chambre régionale de métiers (organismes de formation) → intermédiaires ; SIRET source d'une agence de placement / d'intérim (78.1, 78.2) → intermédiaire. 443 offres LBA concernées. 78.30Z (groupements d'employeurs) gardé comme employeur.

**Résultats / chiffres clés :**
- Offres d'employeurs avec SIRET : 77,5 % ; modèle de réponse 7/7 ; 291 tests.
- Pour le pitch : autour de Rennes, **aucune offre d'alternance data publiée, mais 4 389 entreprises susceptibles d'en accueillir une**.

---

## 2026-11-27 — Données La bonne alternance de production + ajustement T32

**Fait :**
- `collect_lba.py` : d'abord avec une clé **sandbox** → export de recette (972 offres fictives) détecté par l'alerte du collecteur, mis en quarantaine puis supprimé, rien n'a été intégré. Avec la clé **production** : 12 748 offres, 382 180 recruteurs (comme Maxence).
- `build_all.py --share` avec Adzuna + LBA : 23 524 offres, **76,8 %** des offres d'employeurs avec SIRET (65,1 % avant, grâce aux SIRET fournis par LBA), 546 entreprises avec offre data ; modèle de réponse toujours 7/7. `--share` inclut maintenant `lba_recruteurs.parquet` et `lbb.parquet`.
- T32 : les signaux externes (La Bonne Boîte, recruteur LBA) passent avant les rangs centiles (sinon écartés par la limite de 3 raisons). Test ajouté.

**Résultats / chiffres clés :**
- Rennes 20 km, alternance : 204 recruteurs LBA dans la couche orange ; ex. Hellowork (aucune offre data) : « Recommandée car La bonne alternance la repère comme recruteur d'alternants sans offre publiée ; … ».

**Points d'attention pour l'équipe :**
- Une clé LBA **sandbox** donne des données de test : vérifier l'absence d'alerte « RECETTE » à la collecte.

---

## 2026-11-27 — T32 : explication « Recommandée car … »

**Fait :**
- `radar/explain.py` (fonction pure, D29) ; une ligne dans `radar/spontaneous.py` (colonne `explication`) ; popup orange (`_explication_html`). La fiche de Celia l'affiche sans modification. 6 tests (`tests/test_explain.py`).
- Vérification du pipeline après BODACC (Celia) et La Bonne Boîte (Emma) : `collect_lbb.py` + `build_all.py --share`, 6 étapes OK ; fichiers repartagés.

**Résultats / chiffres clés :**
- Exemple : « Recommandée car elle recrute des profils data (2 offres d'emploi en ligne) mais ne propose aucune offre de stage ; son besoin data, rapporté à sa taille, est parmi les plus élevés (top 1 % des entreprises) ; … ».
- Paris 50 km : 76 702 entreprises, classement + explications en 0,9 s (4,0 s si on expliquait tout).

**Points d'attention pour l'équipe :**
- Nouvelle composante de score → ajouter sa raison dans `reasons()`.
- `recruteur_lba` absent de mes données (pas de `lba_recruteurs.parquet` sur mon pod) : la raison LBA n'a été testée que sur données de test.

---

## 2026-11-27 — T35/T36 : modèle de réponse démonstrateur

**Fait :**
- `radar/response/params.yaml` (règle de simulation documentée), `simulate.py` (T35), `model.py` (T36), `scripts/build_response.py` ; étape 5 de `build_all.py` (pipeline complet : 103 s). Schéma `p_reponse_modele` (D7). Décision **D18**. 3 tests (dont une étude de simulation).
- Rapport généré pour le pitch : `docs/MODELE_REPONSE.md`.

**Résultats / chiffres clés :**
- 3 000 étudiants simulés, 45 000 candidatures vers 38 251 établissements réels, 17,7 % de réponses positives.
- Test (étudiants jamais vus) : **AUC 0,646** (plafond 0,692), Brier 0,138, calibration quasi parfaite, **7/7 paramètres retrouvés** dans l'IC 95 % (après atténuation ≈ 0,96 due à l'effet entreprise non observé).

**Points d'attention pour l'équipe :**
- T37 (app) : `p_reponse.parquet` est à distance nulle → ajouter le terme de distance (`modele_reponse.json`) ; bandeau « réponses simulées » obligatoire.
- Les valeurs de `params.yaml` sont des hypothèses : les présenter comme telles.

---

## 2026-11-27 — T50 (pipeline) + T25 (rattrapage du rapprochement)

**Fait :**
- `scripts/build_all.py` : une commande, 51 s, schémas vérifiés à chaque étape ; `--sirene`, `--share`.
- `match_siret.py` : cascade de candidats, alias (morceaux du nom légal), enseignes, noms sans espaces, sigles à points (« S.F.R » perdait son « F » avec les mots vides « H/F » : bug corrigé), préférence ETI/GE entre homonymes. Décision **D15**. 4 tests en plus (137 au total).

**Résultats / chiffres clés :**
- Rapprochement : 63,4 % → **65,1 %** ; entreprises avec offre data : 503 → **523**. SFR, Atos, LCL, GMF, Geodis, Rexel, Radio France retrouvés ; **SFR n'apparaît plus dans la couche orange**.
- API Recherche d'entreprises testée puis écartée : les noms restants sont surtout hors référentiel (L6 mise à jour).

**Points d'attention pour l'équipe :**
- Après toute nouvelle collecte (LBA, Adzuna demain) : `uv run python scripts/build_all.py`.

---

## 2026-11-27 — Limites connues + tâches pour les lever

**Fait :**
- `docs/LIMITES.md` : 16 limites (offres, rapprochement, score, données personnelles), avec impact, réglable ou non, tâche, phrase pour le pitch. Référencé dans `CLAUDE.md` et `PROJET.md`.
- Nouvelles tâches : T25 (rattrapage du rapprochement), T26 (familles de marque), T27 (revue des intermédiaires), T28 (`c_embauche` réel), T18 (autres domaines). T33 marquée faite (via T30), T22 précisée.

---

## 2026-11-27 — T30/T31 : score v0 sur vraies données

**Fait :**
- `radar/score/intensity.py` : gamma-Poisson bayésien empirique (Clayton & Kaldor), a priori par division NAF lissée vers la section. `radar/score/build.py` + `scripts/build_scores.py` → `scores.parquet` (schéma `scores_reels`, D7). Décision **D13**.
- `radar/geo.py` (département → région) ; le collecteur Adzuna écrit `adzuna_couverture.json` (couverture par région), reconstitué pour la collecte du jour.
- 5 tests : l'estimateur retrouve les vrais paramètres sur 20 000 entreprises simulées (moyenne à 3 %), rétrécissement, région non couverte = a priori, contrat.

**Résultats / chiffres clés :**
- 403 550 établissements notés (276 890 entreprises), 54 % dans une zone couverte ; 10 s de calcul.
- A priori les plus élevés : divisions 62 (programmation, 0,28 offre data / 100 salariés), 60, 59, 63.
- Ille-et-Vilaine, sans offre data, top √(intensité × besoin) : France Télévisions, Hellowork, Tessi, Claranet, Luminess, Klaxoon, Ouest-France, SFR.
- 3 entreprises `volume_suspect` (Sanofi, Mistral, Orel Services).

**Points d'attention pour l'équipe :**
- **Maxence (couche orange)** : filtrer `n_offres_domaine_siren == 0` et `volume_suspect == False`, trier par √(c_intensite × c_embauche) ; afficher `couverture == 0` comme « estimation par secteur seulement ».
- Limites : SFR (non rapproché en T21) apparaît « sans offre » ; division 59 (cinéma) proche de l'a priori de sa section.

---

## 2026-11-27 — T21 : rapprochement offres → SIRET + offres.parquet

**Fait :**
- `radar/process/match_siret.py` : intermédiaires écartés (liste + motifs + NAF 78.*), puis exact / sigle (GE seulement) / préfixe / flou ; établissement le plus proche ; règles « loin » (> 50 km) selon la taille et la longueur du nom ; `match_confiance`.
- `radar/process/offres.py` + `scripts/match_offres.py` : relit l'`offres.parquet` d'Emma (T13) et complète seulement les lignes `a_rapprocher` (décision D10). J'avais d'abord refait la classification en double, corrigé. Ajout du **sigle** dans l'extraction SIRENE (EDF, CEA).
- 8 tests sur un mini-référentiel (`tests/test_match_siret.py`) : Air France ≠ France Air, Capgemini → établissement le plus proche, EDF par sigle, homonyme lointain rejeté, intérim = intermédiaire.

**Résultats / chiffres clés :**
- 63,4 % des offres d'employeurs rapprochées (50,5 % haute confiance) ; 16,7 % d'intermédiaires.
- Offres data : 503 entreprises / 622 établissements ; 130 entreprises avec stage ou alternance data.
- Le classement d'Emma est meilleur que mon filtre v0 (écarte « Data Center Technician »).

**Points d'attention pour l'équipe :**
- **Maxence (app)** : utiliser `offres.parquet` (colonne `domaine` d'Emma, `intermediaire`, `siren_match`) plutôt que `quick_filter` ; la couche orange exclut les `siren_match` qui ont une offre du domaine × contrat visé.
- `entreprises.parquet` a été régénéré (colonne `sigle` en plus) → reprendre le nouveau lien.

---

## 2026-11-27 — T20 : référentiel SIRENE + partage S3

**Fait :**
- `radar/collect/sirene.py` + `scripts/extract_sirene.py` : DuckDB lit à distance StockEtablissement + Géolocalisation + StockUniteLegale + NAF rév. 2 → `data/processed/entreprises.parquet` (contrat d'Emma vérifié par `check_columns`). Tests sans réseau : `tests/test_sirene.py`.
- `scripts/share_s3.py` : partage via liens S3 temporaires (24 h) pour les équipiers hors Onyxia ; README de démarrage.

**Résultats / chiffres clés :**
- **406 266 établissements** actifs ≥ 10 salariés, 99,7 % géolocalisés, 99,8 % nommés, 100 % avec libellé NAF ; PME 245 k, ETI 96 k, GE 61 k. Effectifs millésime 2024. Extraction en ~2 min.
- 245 établissements à diffusion partielle → position masquée (RGPD).
- Ajout de `effectif_estime` (moyenne géométrique de la tranche) pour l'exposition du modèle gamma-Poisson.

**Points d'attention pour l'équipe :**
- `ca_n`, `ca_n_1`, `lbb_proba`, `procedure_collective` sont **NA** (pas encore alimentés) : ne pas les traiter comme 0/False dans le score.
- Fichier partagé en lien privé (demander la commande `curl` à Mathis).

---

## 2026-11-27 — T39 : carte couche 1 « Offres réelles »

**Fait :**
- `radar/process/quick_filter.py` : filtre v0 « data » par regex sur le titre + type de contrat déduit du titre (stage / alternance / emploi), en attendant T13. 27 tests (`tests/test_quick_filter.py`).
- `app/streamlit_app.py` : carte folium (OpenStreetMap), **un point bleu par lieu** (taille selon le nombre d'offres, popup listant les offres avec lien vers l'annonce), filtres (contrat visé, régions, mot-clé, ancienneté, « seulement data »), indicateurs, tableau avec liens. Légende prévue pour la couche orange (T40).

**Résultats / chiffres clés :**
- 10 633 offres géolocalisées → **3 298 offres data** (31 %), dont 557 stages et 41 alternances, 1 101 entreprises.
- Seulement 374 positions distinctes (offres placées au centre de la commune) → regroupement par lieu.
- Page de carte ~1 Mo ; titres échappés dans les popups (contenu venant d'Internet).

**Points d'attention pour l'équipe :**
- Les tuiles CartoDB exigent maintenant une clé d'API → utiliser OpenStreetMap.
- Pour T40 : ajouter un `folium.FeatureGroup(name="🟠 Candidature spontanée")` dans `build_map` ; la légende et le contrôle des couches sont déjà en place.
- Pas de capture d'écran possible depuis Claude : à vérifier visuellement via `<URL du service>/proxy/8501/`.

---

## 2026-11-27 — T12 : collecteur Adzuna

**Fait :**
- `radar/collect/adzuna.py` : collecte des offres « data » (< 60 jours) région par région ; cache disque requests-cache (la clé secrète n'est pas stockée dans le cache) ; compteur de quota quotidien (`data/cache/adzuna_quota.json`, arrêt à 240) ; ≤ 25 appels/min ; colonnes alignées sur `radar/schemas.py` (d'Emma) + colonnes propres à Adzuna.
- `scripts/collect_adzuna.py` (options `--regions`, `--max-calls`, `--quota`). Tests sans réseau dans `tests/test_adzuna.py`.

**Résultats / chiffres clés :**
- `data/raw/offres_raw/adzuna.parquet` : **10 776 offres, 2 737 entreprises**, 230 appels utilisés aujourd'hui.
- Complètes : Bretagne (633), Pays de la Loire (1 101), Auvergne-Rhône-Alpes (2 333), Occitanie (1 410). Île-de-France 5 000/14 385 (plafond de 100 pages). Nouvelle-Aquitaine partielle (300). Les autres régions ne sont pas commencées.
- Bruit : « data » dans seulement 23 % des titres. 1 188 titres « stage », 106 « alternance ».
- Variantes de noms (« CREDIT MUTUEL ARKEA » / « Crédit Mutuel Arkéa ») → à normaliser en T21.

**Points d'attention pour l'équipe :**
- Le quota Adzuna du jour est épuisé (230/240) : **ne pas appeler Adzuna aujourd'hui**, utiliser le parquet.
- Le parquet n'est que sur mon pod → à déposer sur S3 pour l'équipe. Ne jamais partager `data/cache/`.

**Prochaine étape :**
- T16 : relancer demain pour compléter (reprise automatique via le cache) et découper l'Île-de-France par département.

---

## 2026-11-27 — T4 : squelette du dépôt

**Fait :**
- `pyproject.toml` (uv, hatchling, ruff, pytest) + `uv.lock` ; package `radar/` avec `collect/`, `process/`, `score/`, `response/`, `llm/`.
- `radar/config.py` : `PATHS` (data/raw, processed, cache), `FILES` (fichiers du contrat), `settings` (clés lues depuis `.env`, jamais affichées ; `settings.require(...)` pour une erreur claire).
- `app/streamlit_app.py` minimal : lit `entreprises.parquet` s'il existe (carte + tableau), sinon message.
- Commandes ajoutées dans `CLAUDE.md` › Stack.

**Vérifié :** `uv sync` OK, ruff OK, `pytest` 2/2, l'app Streamlit démarre et s'affiche sans exception.

**Prochaine étape :**
- T5 (données factices) ou T20 (extraction SIRENE) pour avoir quelque chose à afficher.

---

## 2026-11-27 — Exploration SIRENE (préparation de T20)

**Résultats / chiffres clés :**
- 3 fichiers parquet INSEE sur data.gouv (nov. 2026) : établissements, géolocalisation (lat/lon GPS directement), unités légales (nom). URLs dans `SOURCES.md`.
- DuckDB + httpfs lit à distance : le comptage par tranche d'effectif prend 40 s sans rien télécharger.
- Établissements actifs avec au moins 10 salariés : **~406 000** (≥ 1 salarié : ~1,9 M) → seuil proposé pour `entreprises.parquet`.

**Points d'attention pour l'équipe :**
- Requête d'extraction prête (jointure établissements + géoloc + unités légales) dans la conversation ; T20 reste à prendre.
- RGPD : masquer l'adresse si `statutDiffusionEtablissement = 'P'`.

---

## 2026-11-27 — Test Adzuna (T10)

**Résultats / chiffres clés :**
- Clés OK. France : 1 040 858 offres, dont 35 921 « data » ; « stage data » 812 ; « alternance data » 175 ; Ille-et-Vilaine « data » 508.
- `top_companies` = top 5 seulement → abandonné. `contract_type` rare (14/50) ; description tronquée ; offres anciennes présentes ; cabinets de recrutement fréquents.

**Points d'attention pour l'équipe :**
- Quota ~250 appels/jour : **ne pas lancer de tests Adzuna à la légère**, passer par un cache disque.
- On ne peut pas récupérer toutes les offres d'une entreprise → intensité = nombre d'offres data rapporté à l'effectif (gamma-Poisson), plutôt qu'une part des offres.

---

## 2026-11-27 — Accès France Travail

**Fait :**
- `.env.example` créé ; jeton France Travail OK après souscription aux API.
- Scopes valides : La Bonne Boîte v2, ROME 4.0 Métiers, Marché du travail (non disponibles : Offres d'emploi, ROMEO, Fiches métiers).

**Résultats / chiffres clés :**
- La Bonne Boîte v2 renvoie le SIRET et un `hiring_potential` continu, mais elle couvre mal les métiers data fins (Rennes 30 km : 0 pour M1405 et M1419, 31 pour M1811). Limite de débit : erreur 429 à ~3 req/s.
- Liste des codes ROME 4.0 data dans `SOURCES.md`.

**Points d'attention pour l'équipe :**
- Copier `FT_SCOPES` depuis `.env.example`/`SOURCES.md` dans votre propre `.env`.

---

## 2026-11-27 — Modèle de réponse simulé

**Fait :**
- Décision D6 : modèle de réponse aux candidatures spontanées entraîné sur des réponses simulées (entreprises réelles), affiché comme démonstrateur. Tâches T35–T37.

---

## 2026-11-27 — Cadrage après le retour de l'équipe

**Fait :**
- Prise en compte : 24 h, équipe de 4 (Mathis, Celia, Maxence, Emma), France entière, domaine paramétrable, stage + alternance + emploi, LLM facultatif.
- `TACHES.md` réécrit en liste priorisée (P0 → P3) avec des jalons horaires, sans attribution ; décisions D3–D5 ; architecture et schémas mis à jour.

**Prochaine étape :**
- L'équipe pioche dans les P0 (accès aux API, squelette, données factices, dictionnaire des domaines).

---

## 2026-11-27 — T5 : pitch Radar + inventaire des sources

**Fait :**
- Pitch formalisé dans `docs/PROJET.md` ; architecture proposée et 4 rôles dans `ARCHITECTURE.md` / `TACHES.md`.
- Inventaire des sources dans `docs/SOURCES.md`, avec de vrais appels sur les API ouvertes.

**Résultats / chiffres clés :**
- ⚠️ L'API Offres d'emploi France Travail est **suspendue** (plus exposée sur francetravail.io).
- Recherche d'entreprises : `/near_point` fonctionne ; renvoie NAF, effectif, coordonnées et CA. Dans un rayon de 20 km autour de Rennes : 2 619 établissements en 62.01Z, 1 657 en 62.02A.
- Géocodage Géoplateforme et BODACC : fonctionnent sans clé.
- Ni Adzuna ni France Travail ne fournissent de SIRET → rapprochement nécessaire ; La bonne alternance en fournit.

**Prochaine étape :**
- Créer la clé Adzuna et le jeton La bonne alternance, puis mesurer le volume réel d'offres data dans le 35.

---

## 2026-11-27 — T0 : mise en place de la coordination

**Fait :**
- Création de `CLAUDE.md` (règles communes à toutes les sessions Claude).
- Création de `docs/` : `PROJET.md`, `ARCHITECTURE.md`, `TACHES.md`, `DECISIONS.md`, `journal/`.
- Ajout d'un `.gitignore` (données, secrets, environnements, caches).

**Fichiers touchés :**
- `CLAUDE.md`, `docs/*`, `.gitignore`, `README.md`

**Prochaine étape :**
- Pitch du projet → remplir `docs/PROJET.md` et découper en tâches dans `docs/TACHES.md`.

## 2026-11-28 — T77 : grille LLM secteur × taille × domaine, branchée dans le score

- Reprise de la piste d'Emma (`docs/PISTE_DOMAINES_LLM.md`). `radar/score/llm_grid.py` + `scripts/build_grille_llm.py` (API compatible OpenAI, cache par NAF, JSON validé) + carnet `notebooks/grille_llm_colab.ipynb` (Ollama sur GPU Colab).
- Qwen 2.5 7B sur CPU : trop lent (~35 s/NAF) et notes fausses (banques data 0). Qwen 2.5 14B sur T4 Colab : bon. Consignes v1 (trop de 3) → v2 (cœur de métier sous-noté) → **v3** (retenue). 360 NAF (95 % des établissements) en ~1 h 50 ; les 358 autres en cours.
- Branchement (D45) : la note remplace les indicatrices NAF dans le v1. Validation temporelle : note LLM − témoin +0,025 AUC (significatif), NAF − témoin +0,010 (non) ; LLM − NAF +0,013 (bruit). `docs/EVAL_SCORE.md` mis à jour.
- À faire : relecture à l'aveugle (`data/relecture_grille.csv`), remplacer la grille par les 718 NAF, partager le fichier, afficher la note dans la fiche (@maxence), étendre aux 5 domaines (D21).

## 2026-11-28 — T94 (partie score) : paliers plus sélectifs, carte allégée (D47)

- Diagnostic : score orange = moyenne de rangs centiles (médiane ~0,6), paliers relatifs → 370 « prioritaires » à Rennes, 1 055 à Lyon ; besoin réel très concentré (50 entreprises = 62 % du besoin à Rennes).
- `radar/paliers.py` : seuil absolu de besoin attendu par palier (0,2 / 0,05 / 0,01). `app/carte.py` : `spontaneous_on_map`, paliers 1–2 d'abord, 150 au plus, 20 au moins. Tests dans `tests/test_paliers.py`.
- Après : Rennes 56 prioritaires (carte 145 points, 79 % du besoin), Lyon 195, Guéret 0.
- À faire : valider les seuils avec Celia ; bouton « Voir plus » (Emma) ; piste « classement par besoin attendu en log » si le temps le permet.

## 2026-11-28 — Score orange plus discriminant (D48)

- `c_intensite` et `c_embauche` (proxy) en échelle log absolue (0 = médiane nationale, 1 = 99,5e centile) au lieu de rangs centiles. Rangs gardés dans `rang_intensite` / `rang_embauche` pour les phrases et le modèle de réponse simulé (rapport inchangé).
- Rennes 20 km : médiane 0,60 → 0,21 ; ≥ 0,8 : 289 → 59. Lyon ≥ 0,8 : 1 353 → 191. Tests : `tests/test_embauche.py`.
- ⚠️ Chacun doit relancer `scripts/build_all.py` (scores.parquet hors Git).

## 2026-11-28 — Curseur « Score minimal sur la carte » (D49) + note à l'équipe

- `seuil_carte` (Auto ou ≥ 0,30 … 0,90) dans Filtres › Classement, légende sous la carte ; `spontaneous_on_map(df, min_score)`. Vérifié dans l'app (AppTest, Rennes) : Auto 108 points, ≥ 0,60 107 points, sur 4 281.
- Note « 📣 À lire » en tête de `docs/TACHES.md` (D47–D49, qui doit faire quoi) ; § « Score et carte » dans `docs/GUIDE.md`.

## 2026-11-28 — T77 : grille complète (718 NAF)

- `grille_domaines.parquet` : 718 NAF × 4 tailles × 5 domaines = 14 360 lignes, aucun manquant, doublon ni note invalide, justification partout ; qwen2.5:14b, consigne v3.
- Scores reconstruits (note du NAF propre pour 100 % des établissements) ; `eval_score` : AUC besoin caché 0,845, futur 0,889, conclusion de D45 inchangée.
