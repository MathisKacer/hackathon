# Tâches

> Avant de commencer une tâche : la déplacer dans « En cours » avec ton prénom, committer et pousser **immédiatement** pour éviter que deux personnes fassent la même chose.
> Format : `- [ ] T<num> — description courte — @prenom (si assignée)`

## Découpage en 4 rôles (proposition)

| Rôle | Périmètre | Fichiers produits |
|---|---|---|
| **A — Collecte des offres** | Adzuna, La bonne alternance, ATS ; collecte quotidienne ; classification data/stage ; rapprochement SIRET | `offres_raw/`, `offres.parquet` |
| **B — Référentiel entreprises** | SIRENE Bretagne, finances, BODACC, La Bonne Boîte, Egapro | `entreprises.parquet` |
| **C — Modèle de score** | Bayésien empirique, composantes, validation, explications ; méthodo des slides | `scores.parquet` |
| **D — Application et pitch** | Streamlit, carte, fiche, poids, CV, lettre LLM ; slides et démo | `app/` |

Les rôles C et D commencent sur des **données factices** qui respectent le schéma de `ARCHITECTURE.md`. Ils n'attendent pas A et B.

## 🔴 Priorité haute — à faire (heure 0)

- [ ] T1 — **Demandes d'accès** (prennent du temps, à faire en premier) : clé Adzuna, jeton La bonne alternance, compte francetravail.io (La Bonne Boîte, Marché du travail, ROME ; demande Offres d'emploi via le formulaire) — rôle A
- [ ] T2 — Demander l'export anonymisé des stages au service des stages de l'ENSAI — rôle C
- [ ] T3 — Squelette du dépôt : `pyproject.toml` (uv), package `radar/`, `config.py`, `.env.example`, ruff — rôle D
- [ ] T4 — Générateur de données factices aux schémas du contrat — rôle C

## 🟡 À faire

**A — Offres**
- [ ] T10 — Collecteur Adzuna (Bretagne, requêtes data) + cache, et test du volume réel en Ille-et-Vilaine
- [ ] T11 — Collecteur La bonne alternance (offres + recruteurs potentiels, avec SIRET)
- [ ] T12 — Collecte quotidienne planifiée → S3 (historique)
- [ ] T13 — Classifieur `is_data` / `is_stage` (codes ROME + mots-clés), évalué sur ~100 offres annotées à la main
- [ ] T14 — Rapprochement nom + commune → SIRET (rapidfuzz + Recherche d'entreprises), taux de rapprochement mesuré
- [ ] T15 — Collecteur ATS pour le top des entreprises (slugs Greenhouse, Lever, SmartRecruiters…)

**B — Entreprises**
- [ ] T20 — Extraction SIRENE géolocalisée Bretagne (établissements actifs, employeurs) → `entreprises.parquet`
- [ ] T21 — Enrichissement finances (CA N, N-1) et croissance
- [ ] T22 — Signal BODACC (procédures collectives)
- [ ] T23 — La Bonne Boîte (si l'accès est obtenu)

**C — Score**
- [ ] T30 — Estimation des a priori bêta par secteur + a posteriori + intervalles crédibles
- [ ] T31 — Composantes normalisées et `scores.parquet`
- [ ] T32 — Validation sur les stages ENSAI (AUC, precision@k, références naïves)
- [ ] T33 — Texte d'explication automatique par entreprise (« recommandée car… »)

**D — App et pitch**
- [ ] T40 — Page de recherche : adresse → géocodage → rayon → carte + liste
- [ ] T41 — Curseurs de poids + recalcul du score en direct
- [ ] T42 — Fiche entreprise (décomposition du score, offres, finances, niveau de preuve)
- [ ] T43 — Dépôt du CV → compétences → adéquation (bonus)
- [ ] T44 — Lettre de candidature générée par LLM (bonus)
- [ ] T45 — Slides et scénario de démo

## 🔵 En cours

- _…_

## ✅ Fait

- [x] T0 — Mise en place de la structure de coordination (`CLAUDE.md`, `docs/`) — @mathis
- [x] T5 — Inventaire et test des sources (`docs/SOURCES.md`) — @mathis

## 🧊 Bloqué / en attente

- API Offres d'emploi France Travail : suspendue côté France Travail (voir `SOURCES.md`)
