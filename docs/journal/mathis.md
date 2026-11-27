# Journal — Mathis

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
