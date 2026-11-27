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
- [ ] T2 — Créer le **jeton La bonne alternance** (espace développeurs) → `.env`
- [x] T3 — Compte **francetravail.io** : souscrire à La Bonne Boîte, Marché du travail et ROME 4.0, et envoyer la demande d'accès à Offres d'emploi via le formulaire de contact
- [ ] T6 — **Dictionnaire « domaines »** : pour chaque domaine (data en premier, puis 3 ou 4 autres : finance, marketing, informatique, RH…), ses codes ROME et ses mots-clés → `radar/domains.yaml`

## 🟠 P1 — Chemin critique vers la V1 (H+2 → H+8)

**Offres**
- [x] T10 — 🔗T1 **Test Adzuna** : volume d'offres data en France et dans le 35, champs réellement renvoyés, nombre d'entreprises que renvoie `top_companies` → noter les résultats dans `SOURCES.md`
- [ ] T11 — 🔗T2 **Collecteur La bonne alternance**, France entière : offres + recruteurs potentiels, avec SIRET → `offres_raw/lba/`
- [ ] T12 — 🔗T10 **Collecteur Adzuna** France entière dans la limite du quota (stratégie : `top_companies` par département, requête domaine vs toutes offres) + cache disque → `offres_raw/adzuna/`
- [ ] T13 — 🔗T6 **Classifieur d'offres** : `domaine` (data ou autre), `contrat` (stage / alternance / emploi), à partir du ROME, des mots-clés et du type de contrat

**Entreprises**
- [ ] T20 — **Référentiel SIRENE France** : stock parquet géolocalisé (data.gouv) → établissements actifs et employeurs, avec NAF, tranche d'effectif et lat/lon → `entreprises.parquet` (DuckDB)
- [ ] T21 — 🔗T11,T12 **Rapprochement nom + commune → SIRET** pour les offres Adzuna (rapidfuzz sur le référentiel T20) ; mesurer le taux de rapprochement et le noter dans `SOURCES.md`

**Score**
- [ ] T30 — 🔗T5 **Score v0** sur données factices : composantes simples (part brute des offres du domaine, opportunité cachée, distance, taille) → `scores.parquet`
- [ ] T31 — 🔗T30 **Rétrécissement bêta-binomial** : a priori par secteur NAF, a posteriori, intervalle crédible

**App**
- [ ] T40 — 🔗T4,T5 **Page de recherche** : adresse → géocodage (Géoplateforme) → rayon → carte folium + liste triée
- [ ] T41 — 🔗T40 **Filtres** : domaine, type de contrat visé (stage / alternance / emploi), taille, secteur
- [ ] T42 — 🔗T40 **Curseurs de poids** → recalcul du score en direct

**Intégration**
- [ ] T50 — 🔗T11/T12,T20,T30 **Pipeline `scripts/build_all.py`** : brut → `offres.parquet` → `scores.parquet` ; brancher l'app sur les vraies données (**jalon V1**)

## 🟡 P2 — Valeur ajoutée (H+8 → H+16)

**Modèle de réponse (démonstrateur, réponses simulées)**
- [ ] T35 — 🔗T20 **Simulateur** : règle paramétrique P(réponse | besoin, taille, secteur, distance, historique d'embauche…) dans `radar/response/params.yaml`, tirage des réponses sur les entreprises réelles → `candidatures_simulees.parquet`
- [ ] T36 — 🔗T35 **Modèle de réponse** : logistique (puis arbres boostés si on a le temps) → `p_reponse.parquet` ; slides : calibration, AUC, paramètres retrouvés vs vrais
- [ ] T37 — 🔗T36,T40 Intégration dans l'app : tri par P(réponse) + bandeau « démonstrateur : réponses simulées »

- [ ] T32 — Explication automatique par entreprise (« recommandée car… ») à partir des contributions au score
- [ ] T33 — Modèle gamma-Poisson (nombre d'offres du domaine, avec l'effectif comme exposition) ; comparer au bêta-binomial
- [ ] T34 — **Validation sans vérité terrain** : stabilité du classement (bootstrap), sensibilité aux poids, cohérence avec La Bonne Boîte et la tension du marché → graphiques pour les slides
- [ ] T22 — Enrichissement finances (CA N et N-1, via Recherche d'entreprises ou les ratios INPI) → composante dynamisme
- [ ] T23 — BODACC : écarter ou pénaliser les entreprises en procédure collective
- [ ] T24 — La Bonne Boîte (si l'accès est obtenu) → composante probabilité d'embauche
- [ ] T43 — **Fiche entreprise** : décomposition du score, intervalle crédible, offres récentes, effectif, CA, lien vers l'Annuaire des entreprises
- [ ] T44 — Affichage du **niveau de preuve** (nombre d'offres observées) et du taux de rapprochement global

## 🟢 P3 — Bonus (seulement si le P2 est fini)

- [ ] T45 — Dépôt du CV (PDF) → compétences → composante d'adéquation
- [ ] T46 — Lettre de candidature spontanée générée par LLM (si on trouve une clé ; sinon, modèle à trous)
- [ ] T15 — Collecteur ATS (Greenhouse, Lever, SmartRecruiters) pour le top des entreprises
- [ ] T47 — Temps de trajet en transports en commun (GTFS) au lieu de la distance à vol d'oiseau

## 🎤 Pitch (en continu, une personne référente)

- [ ] T60 — Plan des slides : problème → démo → méthodo du score → limites assumées → suite
- [ ] T61 — Scénario de démo (2 ou 3 recherches qui montrent de bons résultats, dont une hors Bretagne)
- [ ] T62 — 🔗H+18 Cache de démo figé + vidéo de secours
- [ ] T63 — Répétition chronométrée

## 🔵 En cours

- [ ] T5 — **Générateur de données factices** qui respecte les schémas de `ARCHITECTURE.md` (pour que le score et l'app démarrent sans attendre la collecte) — @emma

## ✅ Fait

- [x] T4 — **Squelette du dépôt** : `pyproject.toml` (uv), package `radar/`, `radar/config.py`, `.env.example`, ruff, `app/streamlit_app.py` vide — @mathis
- [x] T0 — Structure de coordination (`CLAUDE.md`, `docs/`) — @mathis
- [x] T00 — Inventaire et test des sources (`docs/SOURCES.md`), architecture proposée — @mathis

## 🧊 Bloqué / en attente

- API Offres d'emploi France Travail : suspendue côté France Travail (voir `SOURCES.md`)
