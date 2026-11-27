# Architecture

> Le « comment ». **Statut : proposition, à valider par l'équipe.** Mettre à jour dès qu'un dossier, un module ou un format de données change.

## Vue d'ensemble

Toute la donnée lourde est **pré-calculée** (batch) sur la Bretagne. L'application ne fait que lire des fichiers parquet : la démo ne dépend d'aucune API au moment où on la présente, sauf pour le géocodage et le LLM, qui ont un repli.

```
            COLLECTE (batch, quotidien)                       TRAITEMENT                     APP
 ┌──────────────────────────────────────────┐
 │ Adzuna · La bonne alternance · ATS       │──► offres_raw/ ──► classification data ─┐
 │ (France Travail si l'accès revient)      │    (parquet daté)  + rapprochement SIRET │
 └──────────────────────────────────────────┘                                          ▼
 ┌──────────────────────────────────────────┐                                    offres.parquet
 │ SIRENE géoloc · Recherche d'entreprises  │──► entreprises.parquet ─────────────────┤
 │ BODACC · finances INPI · La Bonne Boîte  │                                          ▼
 └──────────────────────────────────────────┘                          scoring (bayésien empirique)
                                                                                         ▼
                                                    scores_composantes.parquet ──► Streamlit + folium
                                                                                   (poids utilisateur,
                                                                                    fiche, lettre LLM)
```

## Arborescence cible

```
hackathon/
├── CLAUDE.md
├── docs/                       # PROJET, ARCHITECTURE, SOURCES, TACHES, DECISIONS, journal/
├── pyproject.toml              # dépendances (uv)
├── .env.example                # noms des variables d'environnement (sans valeurs)
├── radar/                      # package Python
│   ├── config.py               # chemins, zone (Bretagne), lecture du .env
│   ├── collect/                # un module par source : adzuna.py, lba.py, ats.py, sirene.py, bodacc.py…
│   ├── process/
│   │   ├── classify.py         # offre data ? stage ? (ROME + mots-clés)
│   │   └── match_siret.py      # rapprochement nom + commune → SIRET
│   ├── score/
│   │   ├── components.py       # intensité data, opportunité cachée, dynamisme, adéquation
│   │   ├── shrinkage.py        # bêta-binomial bayésien empirique
│   │   └── validate.py         # validation sur l'historique des stages ENSAI
│   └── llm/letter.py           # génération de lettre (bonus)
├── app/streamlit_app.py
├── scripts/                    # points d'entrée : collect_daily.py, build_all.py
├── notebooks/                  # exploration (sorties vidées avant commit)
├── tests/
└── data/                       # ignoré par Git : raw/, processed/ (ou S3 Onyxia)
```

## Données et formats intermédiaires (contrat entre coéquipiers)

Tous les fichiers sont en parquet dans `data/processed/` (copie sur S3). **Ne pas changer un schéma sans prévenir l'équipe et mettre à jour ce tableau.**

| Fichier | Produit par | Utilisé par | Colonnes clés |
|---|---|---|---|
| `offres_raw/<source>/<date>.parquet` | collect/* | process | `source, offre_id, date_collecte, titre, description, entreprise_nom, commune, lat, lon, contrat, url, siret (si fourni)` |
| `offres.parquet` | process | score, app | ci-dessus + `is_data: bool, is_stage: bool, siret_match, match_score, match_methode` |
| `entreprises.parquet` | collect/sirene… | process, score, app | `siret, siren, nom, naf, naf_libelle, tranche_effectif, categorie, lat, lon, commune, ca_n, ca_n_1, procedure_collective: bool, lbb_proba` |
| `scores.parquet` | score | app | `siret` + une colonne par composante normalisée dans [0, 1] (`c_intensite, c_cachee, c_dynamisme, c_taille…`) + `n_offres, n_offres_data, intensite_post, intensite_ic_bas, intensite_ic_haut` |

Le score final **n'est pas stocké** : l'app le calcule à la volée, `score = Σ wⱼ · cⱼ`, avec les poids choisis par l'utilisateur. L'adéquation (distance, CV) dépend de l'utilisateur et est aussi calculée dans l'app.

## Modèle de score (détail)

- **Intensité data** de l'entreprise *i* dans le secteur *s* : kᵢ offres data sur nᵢ offres. A priori Beta(αₛ, βₛ) estimé par secteur NAF (méthode des moments ou maximum de vraisemblance bêta-binomial sur les entreprises avec nᵢ ≥ 1). A posteriori : (kᵢ + αₛ) / (nᵢ + αₛ + βₛ), avec un intervalle crédible affiché sur la fiche.
- **Piste à étudier** : modèle gamma-Poisson du *nombre* d'offres data avec l'effectif comme exposition. La part seule ignore le volume, et la plupart des entreprises ont nᵢ = 0.
- **Composantes** ramenées dans [0, 1] par rangs centiles. Le **niveau de preuve** (nᵢ) est affiché pour que l'étudiant voie quand une recommandation repose sur peu d'offres.
- **Validation** (si l'export des stages ENSAI est obtenu) : les entreprises qui ont accueilli des ENSAI sont-elles bien classées ? Mesures : AUC, precision@k, comparaison à des références naïves (tri par effectif, tri par distance).

## Stack technique

- Python ≥ 3.11, gestion des dépendances avec **uv**
- pandas + **DuckDB** sur parquet
- `requests` / `httpx` + cache disque (`requests-cache`) pour économiser les quotas
- `rapidfuzz` pour le rapprochement de noms
- **Streamlit + streamlit-folium** pour l'application
- Planification : GitHub Actions (cron) ou tâche Onyxia pour la collecte quotidienne → S3
- LLM (bonus) : API Claude

## Conventions

- Code et noms en **anglais**, docs et commits en **français** _(à confirmer)_.
- Formatage : `ruff format` + `ruff check`.
- Chemins relatifs à la racine du dépôt via `radar/config.py`, jamais de chemins absolus.
- Secrets dans `.env` (non versionné), noms des variables listés dans `.env.example`.
