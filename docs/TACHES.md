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
- [x] T2 — Créer le **jeton La bonne alternance** (espace développeurs) → `.env` _(fait, signalé par @emma)_
- [x] T3 — Compte **francetravail.io** : souscrire à La Bonne Boîte, Marché du travail et ROME 4.0, et envoyer la demande d'accès à Offres d'emploi via le formulaire de contact

## 🟠 P1 — Chemin critique vers la V1 (H+2 → H+8)

**Offres**
- [x] T10 — 🔗T1 **Test Adzuna** : volume d'offres data en France et dans le 35, champs réellement renvoyés, nombre d'entreprises que renvoie `top_companies` → noter les résultats dans `SOURCES.md`
- [ ] T16 — 🔗T12 **Compléter la collecte Adzuna** : relancer `uv run python scripts/collect_adzuna.py` chaque jour (reprend grâce au cache) ; découper l'Île-de-France par département (5 000/14 385 récupérées, plafond de 100 pages) ; ⚠️ le quota (~240/jour) est **partagé par tous ceux qui utilisent la même clé**
- [ ] T13 — 🔗T6 **Classifieur d'offres** : `domaine` (data ou autre), `contrat` (stage / alternance / emploi), à partir du ROME, des mots-clés et du type de contrat

**Entreprises**
- [ ] T21 — 🔗T11,T12 **Rapprochement nom + commune → SIRET** pour les offres Adzuna (rapidfuzz sur le référentiel T20) ; mesurer le taux de rapprochement et le noter dans `SOURCES.md`

**Score**
- [ ] T30 — 🔗T5 **Score v0** sur données factices : composantes simples (part brute des offres du domaine, opportunité cachée, distance, taille) → `scores.parquet`
- [ ] T31 — 🔗T30 **Rétrécissement bêta-binomial** : a priori par secteur NAF, a posteriori, intervalle crédible

**App**
- [ ] T40 — 🔗T4,T5 **Page de recherche + couche 2 « Candidature spontanée » (orange)** : adresse → géocodage (Géoplateforme) → rayon → même carte folium, entreprises **sans offre correspondante** classées par score ; légende des deux couches + deux listes triées
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

- [ ] T11 — 🔗T2 **Collecteur La bonne alternance**, France entière : offres + recruteurs potentiels, avec SIRET → `offres_raw/lba/` — @maxence

## ✅ Fait

- [x] T20 — **Référentiel SIRENE France** : `uv run python -m radar.collect.sirene` (≈ 40 s, lecture à distance) → `data/processed/entreprises.parquet`, 406 k établissements actifs ≥ 10 salariés, géolocalisés, avec libellé NAF — @celia
- [x] T6 — **Dictionnaire « domaines »** : `radar/domains.yaml` (data, informatique, finance, marketing, rh ; codes ROME 4.0 vérifiés + mots-clés) et `radar/domains.py` (`load_domains`, `classify`) — @emma
- [x] T39 — 🔗T4 **Carte couche 1 « Offres réelles » (bleu)** : afficher les offres de `data/raw/offres_raw/*.parquet` (Adzuna maintenant, La bonne alternance ensuite), avec popup titre / entreprise / lien vers l'annonce ; filtre v0 par mots-clés dans le titre en attendant T13 — @mathis
- [x] T12 — 🔗T10 **Collecteur Adzuna** France entière dans la limite du quota (offres « data » région par région, Bretagne et Île-de-France d'abord, offres de moins de 60 jours) + cache disque + compteur de quota → `data/raw/offres_raw/adzuna.parquet` — @mathis
- [x] T5 — **Générateur de données factices** : `uv run python scripts/make_fake_data.py` → tous les fichiers du contrat dans `data/` (voir `radar/fake_data.py`) — @emma
- [x] T4 — **Squelette du dépôt** : `pyproject.toml` (uv), package `radar/`, `radar/config.py`, `.env.example`, ruff, `app/streamlit_app.py` vide — @mathis
- [x] T0 — Structure de coordination (`CLAUDE.md`, `docs/`) — @mathis
- [x] T00 — Inventaire et test des sources (`docs/SOURCES.md`), architecture proposée — @mathis

## 🧊 Bloqué / en attente

- T7 — 🔗T11 Ajouter des **recruteurs LBA factices** (`lba_recruteurs.parquet`) au générateur T5 — @emma, **après la fusion de la branche de Maxence**
- API Offres d'emploi France Travail : suspendue côté France Travail (voir `SOURCES.md`)
