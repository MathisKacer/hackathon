# Architecture

> Le « comment ». **Statut : proposition, à valider par l'équipe.** Mettre à jour dès qu'un dossier, un module ou un format de données change.

## Vue d'ensemble

Échelle : **France entière**. Hackathon de 24 h → **une seule collecte** (instantané), pas d'historique ni de collecte quotidienne. Toute la donnée lourde est **pré-calculée** (batch). L'application ne fait que lire des fichiers parquet : la démo ne dépend d'aucune API au moment où on la présente, sauf pour le géocodage et le LLM, qui ont un repli.

```
            COLLECTE (batch, quotidien)                       TRAITEMENT                     APP
 ┌──────────────────────────────────────────┐
 │ Adzuna · La bonne alternance · ATS       │──► offres_raw/ ──► domaine × contrat ───┐
 │ (France Travail si l'accès revient)      │    (instantané)    + rapprochement SIRET │
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
│   ├── config.py               # chemins, lecture du .env
│   ├── schemas.py              # colonnes du contrat de données (copie en code du tableau ci-dessous) + check_columns()
│   ├── fake_data.py            # T5 : générateur de données FACTICES respectant le contrat
│   ├── domains.yaml            # domaines (data, finance…) → codes ROME + mots-clés
│   ├── collect/                # un module par source : adzuna.py, lba.py, ats.py, sirene.py, bodacc.py…
│   ├── process/
│   │   ├── classify.py         # domaine de l'offre + type de contrat (stage / alternance / emploi)
│   │   └── match_siret.py      # rapprochement nom + commune → SIRET
│   ├── score/
│   │   ├── components.py       # intensité data, opportunité cachée, dynamisme, adéquation
│   │   ├── shrinkage.py        # bêta-binomial bayésien empirique
│   │   └── validate.py         # stabilité (bootstrap), sensibilité aux poids, cohérence externe
│   ├── response/
│   │   ├── simulate.py         # génère des réponses simulées sur les entreprises réelles
│   │   ├── params.yaml         # vrais paramètres de la simulation (documentés)
│   │   └── model.py            # entraîne le modèle de réponse, calibration, paramètres retrouvés
│   └── llm/letter.py           # génération de lettre (bonus)
├── app/streamlit_app.py
├── scripts/                    # points d'entrée : collect_all.py, build_all.py, make_fake_data.py
├── notebooks/                  # exploration (sorties vidées avant commit)
├── tests/
└── data/                       # ignoré par Git : raw/, processed/ (ou S3 Onyxia)
```

## Données et formats intermédiaires (contrat entre coéquipiers)

Tous les fichiers sont en parquet dans `data/processed/` (copie sur S3), sauf les offres brutes, dans `data/raw/offres_raw/<source>.parquet`. **Ne jamais partager `data/cache/`** (cache HTTP). **Ne pas changer un schéma sans prévenir l'équipe et mettre à jour ce tableau ET `radar/schemas.py`** (vérification : `check_columns(df, "<nom>")`).

Données factices pour développer sans la collecte : `uv run python scripts/make_fake_data.py` (T5). Elles produisent tous les fichiers ci-dessous ; le script refuse d'écraser des fichiers existants sans `--force`.

| Fichier | Produit par | Utilisé par | Colonnes clés |
|---|---|---|---|
| `data/raw/offres_raw/<source>.parquet` | collect/* | process | `source, offre_id, date_collecte, date_publication, titre, description, entreprise_nom, commune, code_postal, lat, lon, contrat_brut, code_rome, url, siret (si fourni)` — ces 15 colonnes en premier, dans cet ordre ; une source peut ajouter ses propres colonnes après (ex. Adzuna : `contrat_temps, categorie, salaire_min, salaire_max, salaire_predit, zone, requete, region_requete`) |
| `offres.parquet` | process | score, app | ci-dessus + `domaine: str` (clé de `domains.yaml` ou `autre`), `contrat: stage/alternance/emploi`, `siret_match, match_score, match_methode` |
| `entreprises.parquet` | collect/sirene… | process, score, app | `siret, siren, nom, naf, naf_libelle, tranche_effectif, categorie, lat, lon, commune, ca_n, ca_n_1, procedure_collective: bool, lbb_proba` |
| `scores.parquet` | score | app | **une ligne par (`siret`, `domaine`)** : composantes dans [0, 1] (`c_intensite, c_dynamisme, c_embauche…`) + `n_offres, n_offres_domaine, n_stage_domaine, n_alternance_domaine, intensite_post, intensite_ic_bas, intensite_ic_haut` |
| `candidatures_simulees.parquet` | response/simulate | response/model | `siret, profil_id, domaine, contrat_vise, distance_km, <variables>, p_vraie, repondu: bool` — **données simulées** |
| `p_reponse.parquet` | response/model | app | `siret, domaine, contrat_vise, p_reponse, contributions…` |

Le score final **n'est pas stocké** : l'app le calcule à la volée, `score = Σ wⱼ · cⱼ`, avec les poids choisis par l'utilisateur. L'adéquation (distance, CV) et l'**opportunité cachée** dépendent de l'utilisateur (contrat visé) et sont calculées dans l'app : opportunité cachée = besoin dans le domaine (offres d'emploi) mais 0 offre du contrat visé (stage ou alternance).

## Modèle de score (détail)

- **Intensité dans le domaine** *d* (data par défaut) de l'entreprise *i* du secteur *s* : kᵢ offres du domaine sur nᵢ offres, **tous contrats confondus** (une offre d'emploi data est un signal de besoin data). A priori Beta(αₛ, βₛ) estimé par secteur NAF (méthode des moments ou maximum de vraisemblance bêta-binomial sur les entreprises avec nᵢ ≥ 1). A posteriori : (kᵢ + αₛ) / (nᵢ + αₛ + βₛ), avec un intervalle crédible affiché sur la fiche.
- **Piste à étudier** : modèle gamma-Poisson du *nombre* d'offres data avec l'effectif comme exposition. La part seule ignore le volume, et la plupart des entreprises ont nᵢ = 0.
- **Composantes** ramenées dans [0, 1] par rangs centiles. Le **niveau de preuve** (nᵢ) est affiché pour que l'étudiant voie quand une recommandation repose sur peu d'offres.
- **Validation sans vérité terrain** : stabilité du top-k par bootstrap sur les offres, sensibilité aux poids, cohérence externe (corrélation avec La Bonne Boîte, avec la tension du marché du travail, et vérification à la main d'un échantillon). Un export de stages d'école permettrait plus tard une vraie validation (AUC, precision@k) : on le cite comme perspective.

## Stack technique

- Python ≥ 3.11, gestion des dépendances avec **uv**
- pandas + **DuckDB** sur parquet
- `requests` / `httpx` + cache disque (`requests-cache`) pour économiser les quotas
- `rapidfuzz` pour le rapprochement de noms
- **Streamlit + streamlit-folium** pour l'application
- Collecte : script unique lancé une fois (instantané), sorties copiées sur S3 Onyxia
- LLM (bonus) : API Claude

## Conventions

- Code et noms en **anglais**, docs et commits en **français**.
- Formatage : `ruff format` + `ruff check`.
- Chemins relatifs à la racine du dépôt via `radar/config.py`, jamais de chemins absolus.
- Secrets dans `.env` (non versionné), noms des variables listés dans `.env.example`.
