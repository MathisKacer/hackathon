# Tâches — 24 h

> **Avant de commencer une tâche** : ajoute `— @prenom` au bout de la ligne, déplace-la dans « En cours », puis commit + push **immédiatement**. Une tâche déjà prise ne se prend pas ; si tu veux aider, demande à la personne qui l'a.
> Équipe : Mathis, Celia, Maxence, Emma. Les tâches ne sont pas encore attribuées : chacun pioche par ordre de priorité.
> 🔗 = dépend d'une autre tâche. Sans 🔗 = démarrable tout de suite.

## Jalons

| Heure | Jalon | Critère |
|---|---|---|
| **H+2** | Accès obtenus + squelette du dépôt + données factices | `uv run streamlit run app/streamlit_app.py` affiche une carte avec des entreprises factices |
| **H+8** | **V1 de bout en bout** | Vraies données (même partielles) → vrai score → app. Rien d'élégant, mais tout marche |
| **H+16** | V2 | Score bayésien complet, fiche entreprise, filtres, France entière |
| **H+18** | 🧊 **Gel des fonctionnalités** | Après ça : corrections de bugs, cache de démo, slides. Pas de nouvelle fonctionnalité |
| **H+22** | Répétition de la démo | Démo enregistrée en vidéo, en secours si le réseau tombe |

## 🔴 P0 — Tout de suite (H+0 → H+2)

- [x] T1 — Créer la **clé Adzuna** (developer.adzuna.com) → l'ajouter au `.env`
- [x] T2 — Créer le **jeton La bonne alternance** (espace développeurs) → `.env` _(fait, signalé par @emma)_ — @celia (jeton à demander à Celia en message privé)
- [x] T3 — Compte **francetravail.io** : souscrire à La Bonne Boîte, Marché du travail et ROME 4.0, et envoyer la demande d'accès à Offres d'emploi via le formulaire de contact

## 🟠 P1 — Chemin critique vers la V1 (H+2 → H+8)

**Offres**
- [x] T10 — 🔗T1 **Test Adzuna** : volume d'offres data en France et dans le 35, champs réellement renvoyés, nombre d'entreprises que renvoie `top_companies` → noter les résultats dans `SOURCES.md`
- [ ] T16 — 🔗T12 **Compléter la collecte Adzuna** : relancer `uv run python scripts/collect_adzuna.py` chaque jour (reprend grâce au cache) ; découper l'Île-de-France par département (5 000/14 385 récupérées, plafond de 100 pages) ; ⚠️ le quota (~240/jour) est **partagé par tous ceux qui utilisent la même clé**

**Entreprises**

**Score**

**App**
- [ ] T51 — 🔗T40,T17 **Recruteurs LBA dans la couche orange** : quand le contrat visé est l'alternance, marquer (ou bonifier) les entreprises présentes dans `lba_recruteurs.parquet` avec un ROME du domaine (signal « recrute des alternants sans offre publiée »)
- [ ] T53 — 🔗T36 `scripts/build_response.py` plante (« Singular matrix ») si les scores sont construits **sans les offres Adzuna** (LBA seules : `c_intensite` et `c_embauche` constantes) → message clair, ou retirer les variables constantes avant l'ajustement (vu par @maxence en T37)

**Intégration**

## 🟡 P2 — Valeur ajoutée (H+8 → H+16)

**Lever les limites connues (voir `docs/LIMITES.md`)**
- [ ] T26 — 🔗T21 **Familles de marque** (L7) : une entreprise ETI/GE dont une entité a des offres du domaine → ses autres entités (même début de nom) sont exclues de la couche orange (`a_offre_groupe`)
- [ ] T27 — 🔗T21 **Revue des intermédiaires** (L8) : passer en revue les plus gros émetteurs + `volume_suspect`, compléter `INTERMEDIARIES` ; à refaire à chaque nouvelle source (LBA)
- [ ] T28 — 🔗T30 **`c_embauche` réel** (L11) : La Bonne Boîte v2 (codes ROME data × départements, ≤ 1 req/s, SIRET fourni) + recruteurs potentiels LBA (T17) ; remplace le proxy
- [ ] T18 — 🔗T16 **Autres domaines** (L1) : collecter Adzuna sur d'autres requêtes (finance, marketing…) avec le quota des jours suivants, Bretagne + grandes villes d'abord ; puis noter ces domaines (`SCORED_DOMAINS`)

**Modèle de réponse (démonstrateur, réponses simulées)**

- [ ] T32 — Explication automatique par entreprise (« recommandée car… ») à partir des contributions au score
- [ ] T34 — **Validation sans vérité terrain** : stabilité du classement (bootstrap), sensibilité aux poids, cohérence avec La Bonne Boîte et la tension du marché → graphiques pour les slides
- [ ] T22 — Enrichissement finances (CA N et N-1, via Recherche d'entreprises ou les ratios INPI) → composante dynamisme (L10 : privilégier les ratios INPI en masse, pas 276 000 appels d'API)
- [ ] T24 — La Bonne Boîte (si l'accès est obtenu) → composante probabilité d'embauche
- [ ] T43 — **Fiche entreprise** : décomposition du score, intervalle crédible, offres récentes, effectif, CA, lien vers l'Annuaire des entreprises
- [ ] T9 — 🔗T6,T8 **Nouvelles catégories de métiers (domaines)** dans `radar/domains.yaml`. Pistes tirées des offres encore classées `autre` après T8 (36,6 %) : **commercial / vente** (Account Executive, SDR, conseiller commercial, business developer), **ingénierie / industrie** (CVC-PLB, automaticien, QARA, FPGA), **santé / recherche clinique** (CRA, clinical trial, pharmacovigilance), **gestion de projet / conseil** (Project Manager, PMO, Chief of Staff), **immobilier**. Pour chacune : codes ROME 4.0 vérifiés via l'API (comme T6) + mots-clés FR/EN, mesure avant/après sur les vraies offres, tests ; garder `fake_data.DOMAINS` aligné (un test le vérifie). Pour qu'une catégorie soit **notée**, il suffit techniquement de l'ajouter à `SCORED_DOMAINS` (`radar/score/build.py`, le calcul est générique), puis au choix du domaine dans l'app. ⚠️ Mais les offres Adzuna viennent toutes de la recherche « data » (D13) : pour un autre domaine, le score ne compterait que les offres qui mentionnent « data » (biais). Options : (a) noter tout de suite avec la mention « signal partiel » ; (b) s'appuyer sur La bonne alternance (offres + recruteurs, tous métiers, codes ROME) ; (c) collecter Adzuna par domaine (quota). À trancher avec @mathis (score) et @maxence (app) : **proposition D21** (LBA pour tous les domaines + Adzuna en « signal partiel »)
- [ ] T44 — Affichage du **niveau de preuve** (nombre d'offres observées) et du taux de rapprochement global

**Comptes (optionnels, D14) : le mode démo anonyme reste le parcours par défaut**
- [ ] T19 — **Données factices vs vraies offres** : dans `fake_data`, `date_collecte` est une date alors que les offres Adzuna l'ont en texte → l'app plante sur les données factices (`offers['date_collecte'].max()[:10]`, dernière ligne de `streamlit_app.py`) et elles n'ont pas `region_requete`. Aligner l'un ou l'autre

## 🟢 P3 — Bonus (seulement si le P2 est fini)

- [ ] T45 — Dépôt du CV (PDF) → compétences → composante d'adéquation
- [ ] T46 — Lettre de candidature spontanée générée par LLM (si on trouve une clé ; sinon, modèle à trous)
- [ ] T15 — Collecteur ATS (Greenhouse, Lever, SmartRecruiters) pour le top des entreprises
- [ ] T47 — Temps de trajet en transports en commun (GTFS) au lieu de la distance à vol d'oiseau
- [ ] T52 — 🔗T48 _(très optionnel, seulement si tout le reste est fini)_ **Base des comptes hébergée (Supabase, région UE)** : comptes, profils et historique partagés par toute l'équipe et sauvegardés (aujourd'hui : un fichier SQLite par pod, L17). Adapter `radar/accounts.py` à PostgreSQL (URL de connexion dans le `.env`), **garder SQLite en repli automatique** si Supabase ne répond pas (la démo ne doit pas en dépendre) ; vérifier d'abord que le SSP Cloud laisse sortir vers le port 5432/6543. En option : Supabase Auth pour « mot de passe oublié » (L18). Mettre à jour `docs/SECURITE.md` (données chez un tiers). Sinon : à présenter comme perspective au pitch

## 🎤 Pitch (en continu, une personne référente)

- [ ] T60 — Plan des slides : problème → démo → méthodo du score → limites assumées → suite
- [ ] T61 — Scénario de démo (2 ou 3 recherches qui montrent de bons résultats, dont une hors Bretagne)
- [ ] T62 — 🔗H+18 Cache de démo figé + vidéo de secours
- [ ] T63 — Répétition chronométrée

## 🔵 En cours

- [ ] T23 — BODACC : écarter ou pénaliser les entreprises en procédure collective — @celia
- _…_

## ✅ Fait

- [x] T37 — 🔗T36,T40 Intégration dans l'app : tri par P(réponse) + bandeau « démonstrateur : réponses simulées » — @maxence → `radar/response/predict.py` (SIRET affichés, + distance au logit), réglage « Classer par Score / P(réponse) simulée », colonne et fiche, bandeau ; emploi non couvert, « Tous » = moyenne stage/alternance ; D23
- [x] T42 — 🔗T40 **Curseurs de poids** → recalcul du score en direct — @maxence → 5 curseurs 0–5 (intensité, besoin attendu, proximité, opportunité cachée, dynamisme), score = moyenne pondérée, apport de chaque composante dans la liste et la fiche, bouton « Poids par défaut », enregistrés au profil ; D22
- [x] T41 — 🔗T40 **Filtres** : domaine, type de contrat visé (stage / alternance / emploi), taille, secteur — @maxence → domaines lus dans `domains.yaml` (offres 🔵 classées par ROME + titre, score 🟠 du domaine), taille en 4 tranches et secteur NAF (multi-choix, couche 🟠, L20) ; `radar/filters.py`, enregistrés dans le profil ; D20
- [x] T40 — 🔗T4,T5 **Page de recherche + couche 2 « Candidature spontanée » (orange)** : adresse → géocodage (Géoplateforme) → rayon → même carte folium, entreprises **sans offre correspondante** classées par score ; légende des deux couches + deux listes triées — @maxence → `radar/spontaneous.py` (DuckDB, exclusion par contrat visé au niveau SIREN, score D13) + `radar/geocode.py` (Géoplateforme, cache disque) ; D19
- [x] T36 — 🔗T35 **Modèle de réponse** : logistique (puis arbres boostés si on a le temps) → `p_reponse.parquet` ; slides : calibration, AUC, paramètres retrouvés vs vrais — @mathis → AUC 0,646, 7/7 paramètres retrouvés, rapport `docs/MODELE_REPONSE.md`
- [x] T35 — 🔗T20 **Simulateur** : règle paramétrique P(réponse | besoin, taille, secteur, distance, historique d'embauche…) dans `radar/response/params.yaml`, tirage des réponses sur les entreprises réelles → `candidatures_simulees.parquet` — @mathis → `radar/response/simulate.py` + `params.yaml`
- [x] T8 — **Titres anglais** : mots-clés anglais ajoutés dans `domains.yaml` après mesure sur les 10 776 vraies offres Adzuna ; offres « autre » 41,6 % → 36,6 % (D17) — @emma
- [x] T48 (suite) — **Sécurité des mots de passe** (D16, `docs/SECURITE.md`) : 12 caractères min. et 3 types de caractères, liste noire, identifiant interdit, blocage du compte 15 min après 5 échecs (en base, résiste au rechargement) — @celia
- [x] T49 — **Historique des recherches** (connecté seulement, D14) : chaque recherche enregistrée (paramètres, nombre de résultats, 5 premières entreprises) ; « 🕘 Mes recherches » en bas de la barre latérale avec « ↻ Relancer » et « Effacer mon historique » ; ajustements à moins de 2 min fusionnés, 50 max par compte. `top=` reçoit les noms des premières entreprises orange (affichés tels quels) — @celia
- [x] T25 — 🔗T21 **Rattrapage du rapprochement** (L6, L9) : pour les noms non rapprochés (~1 200), API Recherche d'entreprises (`/search?q=<nom>` + proximité ; gère sigles et noms commerciaux, ~7 req/s) + table d'alias manuelle pour les 30 plus gros émetteurs (SFR, EY, Pennylane…) ; objectif : SFR & co ne sortent plus en orange — @mathis → local (cascade, alias, enseigne, sigles à points, préférence ETI/GE) : 63,4 % → 65,1 %, SFR/Atos/LCL/GMF/Geodis retrouvés ; API écartée (voir L6)
- [x] T50 — 🔗T11/T12,T20,T30 **Pipeline `scripts/build_all.py`** : brut → `offres.parquet` → `scores.parquet` ; brancher l'app sur les vraies données (**jalon V1**) — @mathis → `uv run python scripts/build_all.py` (51 s, schémas vérifiés, `--sirene`, `--share`)
- [x] T48 — **Connexion facultative + profil** (D14) : mode démo anonyme par défaut ; bloc compte dans la barre latérale (connexion, création, enregistrer le profil, déconnexion, suppression) ; `radar/accounts.py` + `app/compte.py`, SQLite `data/app/radar.db`, mots de passe scrypt. ⚠️ **T40/T41/T42** : donner une `key` à chaque nouveau réglage et l'ajouter à `PROFILE_KEYS` dans `app/streamlit_app.py` — @celia
- [x] T33 — Modèle gamma-Poisson (nombre d'offres du domaine, avec l'effectif comme exposition) ; comparer au bêta-binomial → fait dans T30 (D13)
- [x] T17 — 🔗T11 **Partager les données LBA sur S3** (`offres_raw/lba.parquet`, `lba_recruteurs.parquet`) : relancer `scripts/collect_lba.py` sur Onyxia puis `scripts/share_s3.py` — @maxence → déposés sur S3 (espace privé de Maxence, liens 24 h envoyés en MP) ; ⚠️ `share_s3.py` se lance avec `python3` (système Onyxia), pas `uv run` (botocore absent du venv)
- [x] T31 — 🔗T30 **Rétrécissement bêta-binomial** : a priori par secteur NAF, a posteriori, intervalle crédible — @mathis → fusionnée dans T30 : gamma-Poisson au lieu de bêta-binomial (D13)
- [x] T30 — 🔗T5 **Score v0** sur données factices : composantes simples (part brute des offres du domaine, opportunité cachée, distance, taille) → `scores.parquet` — @mathis → gamma-Poisson réel (D13), `scripts/build_scores.py`
- [x] T7 — **Recruteurs LBA factices** : `make_fake_data.py` écrit aussi `data/raw/lba_recruteurs.parquet` (schéma `recruteurs_lba`, codes ROME réels de `domains.yaml`) — @emma
- [x] T21 — 🔗T11,T12 **Rapprochement nom + commune → SIRET** pour les offres Adzuna (rapidfuzz sur le référentiel T20) ; mesurer le taux de rapprochement et le noter dans `SOURCES.md` — @mathis → **63 % des offres d'employeurs rapprochées** (50 % confiance haute), intermédiaires écartés (17 %) ; pipeline D10 : `classify_offres.py` (Emma) puis `match_offres.py` complète `offres.parquet`
- [x] T13 — **Classifieur d'offres** : `uv run python scripts/classify_offres.py` → `offres.parquet` avec `domaine`, `contrat`, la règle qui a décidé et le SIRET donné par la source ; les offres Adzuna restent `a_rapprocher` pour T21 — @emma
- [x] T11 — **Collecteur La bonne alternance** (export complet France) : `uv run python scripts/collect_lba.py` → `data/raw/offres_raw/lba.parquet` (12 748 offres) + `data/raw/lba_recruteurs.parquet` (382 180 recruteurs potentiels, dont 28 845 avec un ROME data) — @maxence
- [x] T20 — **Référentiel SIRENE France** : stock parquet géolocalisé (data.gouv) → établissements actifs et employeurs, avec NAF, tranche d'effectif et lat/lon → `entreprises.parquet` (DuckDB) — @mathis et @celia (deux versions fusionnées, D11) : `uv run python scripts/extract_sirene.py [--dep 35]` → 406 266 établissements
- [x] T6 — **Dictionnaire « domaines »** : `radar/domains.yaml` (data, informatique, finance, marketing, rh ; codes ROME 4.0 vérifiés + mots-clés) et `radar/domains.py` (`load_domains`, `classify`) — @emma
- [x] T39 — 🔗T4 **Carte couche 1 « Offres réelles » (bleu)** : afficher les offres de `data/raw/offres_raw/*.parquet` (Adzuna maintenant, La bonne alternance ensuite), avec popup titre / entreprise / lien vers l'annonce ; filtre v0 par mots-clés dans le titre en attendant T13 — @mathis
- [x] T12 — 🔗T10 **Collecteur Adzuna** France entière dans la limite du quota (offres « data » région par région, Bretagne et Île-de-France d'abord, offres de moins de 60 jours) + cache disque + compteur de quota → `data/raw/offres_raw/adzuna.parquet` — @mathis
- [x] T5 — **Générateur de données factices** : `uv run python scripts/make_fake_data.py` → tous les fichiers du contrat dans `data/` (voir `radar/fake_data.py`) — @emma
- [x] T4 — **Squelette du dépôt** : `pyproject.toml` (uv), package `radar/`, `radar/config.py`, `.env.example`, ruff, `app/streamlit_app.py` vide — @mathis
- [x] T0 — Structure de coordination (`CLAUDE.md`, `docs/`) — @mathis
- [x] T00 — Inventaire et test des sources (`docs/SOURCES.md`), architecture proposée — @mathis

## 🧊 Bloqué / en attente

- T14 — 🔗T13,T8 **Tester l'API ROMEO** (France Travail : intitulé de poste → codes ROME + score de confiance) pour classer les offres Adzuna, qui n'ont pas de code ROME. Test sur ~100 titres classés `autre` par `classify` (3 225 titres distincts « autre » sur 8 710) : ROMEO fait-il mieux que les mots-clés, y compris sur les titres anglais ? Noter débit, intitulés par appel et délai d'accès dans `SOURCES.md`. Si concluant : code ROME ROMEO en entrée de `classify` (cache par titre), ce qui simplifie T9 — @emma, **en attente : @mathis doit ajouter ROMEO aux abonnements de l'application sur francetravail.io** (scope absent aujourd'hui)
- API Offres d'emploi France Travail : suspendue côté France Travail (voir `SOURCES.md`)
