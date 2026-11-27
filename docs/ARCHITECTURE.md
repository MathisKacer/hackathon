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
│   ├── accounts.py             # T48/T49 : comptes facultatifs, profils et historique (SQLite data/app/radar.db, scrypt)
│   ├── schemas.py              # colonnes du contrat de données (copie en code du tableau ci-dessous) + check_columns()
│   ├── fake_data.py            # T5 : générateur de données FACTICES respectant le contrat
│   ├── domains.yaml            # T6 : domaines (data, informatique, finance, marketing, rh) → codes ROME 4.0 + mots-clés
│   ├── domains.py              # chargement de domains.yaml + classify(titre, code_rome) → domaine (base de T13)
│   ├── geocode.py              # T40 : adresse → lat/lon (Géoplateforme IGN, sans clé, cache disque PATHS.cache)
│   ├── filters.py              # T41 : filtres taille (4 tranches) et secteur (section NAF) des entreprises (D20)
│   ├── spontaneous.py          # T40 : couche orange — entreprises du rayon sans offre correspondante, classées (D19)
│   ├── collect/                # un module par source : adzuna.py, lba.py, ats.py, sirene.py, bodacc.py…
│   ├── process/
│   │   ├── classify.py         # T13 : domaine (radar.domains.classify) + contrat + SIRET donné par la source → offres.parquet
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
├── app/streamlit_app.py        # + app/compte.py : bloc « compte » et « Mes recherches » de la barre latérale (T48, T49)
├── scripts/                    # points d'entrée : collect_all.py, build_all.py, make_fake_data.py
├── notebooks/                  # exploration (sorties vidées avant commit)
├── tests/
└── data/                       # ignoré par Git : raw/, processed/ (ou S3 Onyxia)
```

## Données et formats intermédiaires (contrat entre coéquipiers)

Tous les fichiers sont en parquet dans `data/processed/` (copie sur S3), sauf les offres brutes, dans `data/raw/offres_raw/<source>.parquet`. **Ne jamais partager `data/cache/`** (cache HTTP). **Ne pas changer un schéma sans prévenir l'équipe et mettre à jour ce tableau ET `radar/schemas.py`** (vérification : `check_columns(df, "<nom>")`).

Données factices pour développer sans la collecte : `uv run python scripts/make_fake_data.py` (T5 ; recruteurs LBA ajoutés par T7). Elles produisent tous les fichiers ci-dessous ; le script refuse d'écraser des fichiers existants sans `--force`.

| Fichier | Produit par | Utilisé par | Colonnes clés |
|---|---|---|---|
| `data/raw/offres_raw/<source>.parquet` | collect/* | process | `source, offre_id, date_collecte, date_publication, titre, description, entreprise_nom, commune, code_postal, lat, lon, contrat_brut, code_rome, url, siret (si fourni)` — ces 15 colonnes en premier, dans cet ordre ; une source peut ajouter ses propres colonnes après (ex. Adzuna : `contrat_temps, categorie, salaire_min, salaire_max, salaire_predit, zone, requete, region_requete`) ; LBA : `partenaire, naf, naf_libelle, taille, adresse, niveau_diplome, nb_postes, statut, date_expiration, date_debut, duree_mois, teletravail, delegue_ecole` (si `delegue_ecole` est vrai, le SIRET est celui de l'école) |
| `data/raw/lba_recruteurs.parquet` | collect/lba | score, app | `source, recruteur_id, date_collecte, siret, nom, raison_sociale, naf, naf_libelle, taille, adresse, code_postal, commune, lat, lon, site_web, opco, idcc, code_rome, url` — « recruteurs potentiels » LBA : entreprises **sans offre publiée** susceptibles d'embaucher des alternants (signal d'opportunité cachée) |
| `offres.parquet` | process | score, app | ci-dessus + `domaine: str` (clé de `domains.yaml` ou `autre`), `contrat: stage/alternance/emploi`, `siret_match, match_score, match_methode` ; en plus : `domaine_regle` (`rome_partiel+titre` / `rome` / `titre` / `aucune`), `contrat_regle` (`contrat_brut` / `titre` / `defaut`). `match_methode` : `siret_source` (SIRET donné par LBA, score 100), `siret_ecole_exclu` (offre déléguée à une école : SIRET retiré), `a_rapprocher` (à compléter par T21), puis les valeurs de T21 ; **après T21** (schéma `offres_rapprochees` dans `radar/schemas.py`, D7/D10) : `siren_match, match_confiance` (haute / moyenne), `match_distance_km, intermediaire` (plateformes / cabinets / intérim : pas de SIRET, voulu). `match_methode` ∈ exact, prefixe, sigle, flou, (…_loin), source, intermediaire, aucun |
| `entreprises.parquet` | collect/sirene… | process, score, app | `siret, siren, nom, naf, naf_libelle, tranche_effectif, categorie, lat, lon, commune, ca_n, ca_n_1, procedure_collective: bool, lbb_proba` ; extras T20 : `nom_etablissement, annee_effectif, code_commune, code_postal, departement, siege, diffusion_partielle, qualite_xy, naf_section, naf_section_libelle, naf_division, effectif_min, effectif_max, effectif_estime, tranche_libelle, adresse` (adresse vide si diffusion partielle ; effectif_estime = valeur centrale géométrique de la tranche, exposition du modèle). `ca_n, ca_n_1, lbb_proba, procedure_collective` = **manquants** (NA) tant que T22–T24 ne sont pas faites |
| `scores.parquet` | score | app | **une ligne par (`siret`, `domaine`)** : composantes dans [0, 1] (`c_intensite, c_dynamisme, c_embauche…`) + `n_offres, n_offres_domaine, n_stage_domaine, n_alternance_domaine, intensite_post, intensite_ic_bas, intensite_ic_haut` ; **réel (T30)** : schéma `scores_reels` (+ `siren, couverture, prior_moyenne, besoin_attendu, n_*_domaine_siren, volume_suspect, c_embauche_source, c_dynamisme_disponible`), domaine data seulement, `intensite_*` en offres pour 100 salariés |
| `candidatures_simulees.parquet` | response/simulate | response/model | `siret, profil_id, domaine, contrat_vise, distance_km, <variables>, p_vraie, repondu: bool` — **données simulées** ; produit par `radar/response/simulate.py` (T35), règle dans `radar/response/params.yaml`, + `siren, ville, c_intensite, c_embauche, log10_effectif, distance_10km, alternance, a_offre_domaine, u_entreprise, donnees_simulees` |
| `p_reponse.parquet` | response/model | app | `siret, domaine, contrat_vise, p_reponse, contributions…` ; **réel (T36)** : schéma `p_reponse_modele` (+ `donnees_simulees`, `contrib_*`), à distance nulle ; distance ajoutée par l'app via `data/processed/modele_reponse.json` |

**Comptes (T48, D14)** : `data/app/radar.db` (SQLite, jamais dans Git ni sur S3) — tables `users(id, username, password_hash, created_at)`, `profils(user_id, data JSON, updated_at)` et `recherches(id, user_id, created_at, params JSON, n_resultats, top_resultats JSON)` (T49 : 50 max par compte, ajustements à moins de 2 min fusionnés). Rien n'y est écrit en mode anonyme.

Le score final **n'est pas stocké** : l'app le calcule à la volée, `score = Σ wⱼ · cⱼ`, avec les poids choisis par l'utilisateur. L'adéquation (distance, CV) et l'**opportunité cachée** dépendent de l'utilisateur (contrat visé) et sont calculées dans l'app : opportunité cachée = besoin dans le domaine (offres d'emploi) mais 0 offre du contrat visé (stage ou alternance).

## Modèle de score (détail)

Voir **D13** dans `DECISIONS.md` (le bêta-binomial initialement prévu a été remplacé).

- **Intensité dans le domaine** (data) de l'entreprise i : k_i offres data observées, exposition E_i = Σ effectif × couverture de la région / 100. k_i ~ Poisson(λ_i E_i), λ_i ~ Gamma(α_s, β_s) par **division NAF**, lissée vers la section puis la moyenne globale ; a priori par la méthode des moments de Clayton & Kaldor. A posteriori Gamma(α_s + k_i, β_s + E_i) : moyenne et intervalle crédible à 90 % (offres data pour 100 salariés).
- **Composantes** dans [0, 1] par rangs centiles : `c_intensite` (λ a posteriori), `c_embauche` (besoin attendu de l'établissement, proxy en attendant La Bonne Boîte), `c_dynamisme` (neutre 0,5 en attendant T22).
- **Couche orange** : entreprises sans offre data (`n_offres_domaine_siren == 0`), hors `volume_suspect`, triées par la moyenne pondérée des composantes (intensité, besoin attendu, proximité, opportunité cachée, dynamisme) avec les poids de l'utilisateur (T42, D22) ; apports `apport_<c>` affichés ; tous les poids à 0 → √(c_intensite × c_embauche) (D13).
- **Validation** : l'estimateur retrouve les paramètres sur données simulées (test) ; à faire pour les slides : stabilité du top-k par bootstrap, sensibilité aux poids.
- **Code** : `radar/score/intensity.py` (modèle), `radar/score/build.py` (assemblage), `scripts/build_scores.py`.

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
