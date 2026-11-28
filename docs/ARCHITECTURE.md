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
│   ├── admin.py                # T79 : administrateurs (équipe, nommés par scripts/admin.py), gestion des comptes, journal (D39)
│   ├── candidature.py          # T78 : candidature spontanée sans ville (verdict selon le contrat, besoin, LBA, groupe) (D38)
│   ├── communes.py             # T55 : communes « Nom (CP) » pour le suggesteur de ville (geo.api.gouv.fr, cache ; repli référentiel) (D28)
│   ├── geocode.py              # T40 : adresse → lat/lon (Géoplateforme IGN, sans clé, cache disque PATHS.cache)
│   ├── familles.py             # T26 : familles de marque (ETI/GE, début du nom) → offres publiées par les sociétés sœurs (D36)
│   ├── filters.py              # T41 : filtres taille (4 tranches) et secteur (section NAF) des entreprises (D20)
│   ├── competences.py          # T45, T80 : compétences du CV (PDF) et correspondance avec l'entreprise, hors score (D37, D40)
│   ├── niveau.py               # T67 : niveau d'études attendu d'une offre (champ LBA, sinon lu dans le texte) (D34)
│   ├── paliers.py              # T65 : score → paliers de priorité (mots, couleurs), règle mixte rang + minimum (D32)
│   ├── recruteurs.py           # T51 : recruteurs potentiels LBA sur un ROME du domaine → `recruteur_lba` (D26)
│   ├── spontaneous.py          # T40 : couche orange — entreprises du rayon sans offre correspondante, classées (D19)
│   ├── procedures.py           # T23 : pénalité et alerte BODACC selon la situation et le contrat (D24)
│   ├── fiche.py                # T43 : données de la fiche (site : SIRENE, offres, BODACC, niveau de preuve, La Bonne Boîte ; entreprise T57 : company_sites, company_summary)
│   ├── export.py               # T91 : export CSV des candidatures
│   ├── recherche.py            # D30 : recherche d'entreprises par nom / SIREN / SIRET, tolérante aux fautes
│   ├── collect/                # un module par source : adzuna.py, lba.py, lbb.py (La Bonne Boîte, T28), sirene.py, bodacc.py…
│   ├── process/
│   │   ├── classify.py         # T13 : domaine (radar.domains.classify) + contrat + SIRET donné par la source → offres.parquet
│   │   └── match_siret.py      # rapprochement nom + commune → SIRET
│   ├── score/
│   │   ├── embauche.py         # T28 : c_embauche = La Bonne Boîte d'abord, proxy « besoin attendu » ensuite (D27)
│   │   ├── components.py       # intensité data, opportunité cachée, dynamisme, adéquation
│   │   ├── shrinkage.py        # bêta-binomial bayésien empirique
│   │   └── validate.py         # stabilité (bootstrap), sensibilité aux poids, cohérence externe
│   ├── response/
│   │   ├── simulate.py         # génère des réponses simulées sur les entreprises réelles
│   │   ├── params.yaml         # vrais paramètres de la simulation (documentés)
│   │   ├── model.py            # entraîne le modèle de réponse, calibration, paramètres retrouvés
│   │   └── predict.py          # T37 : P(réponse) dans l'app (lecture DuckDB des SIRET affichés + effet de la distance, D23)
│   └── llm/letter.py           # génération de lettre (bonus)
├── app/streamlit_app.py        # point d'entrée : navigation en haut, 3 pages (D30)
├── app/vues/                   # explorer.py (carte, listes), entreprises.py (recherche), mon_espace.py (compte)
├── app/commun.py, carte.py     # données et réglages partagés ; carte folium + popup
├── app/fiche_ui.py, compte.py  # fiche entreprise (fenêtre) ; comptes et historique
├── app/cv_ui.py                # T45, T83 : dépôt du CV + liste des compétences (saisie libre), Explorer et Mon espace (D42)
├── app/favoris.py              # T54 : favoris (étoile), temporaires en anonyme, repris à la connexion
├── app/style.py                # T70 : CSS commun, bandeau d'en-tête, tuiles de chiffres, pastilles
├── scripts/                    # points d'entrée : collect_all.py, build_all.py, make_fake_data.py
├── notebooks/                  # exploration (sorties vidées avant commit)
├── tests/
└── data/                       # ignoré par Git : raw/, processed/ (ou S3 Onyxia)
```

## Données et formats intermédiaires (contrat entre coéquipiers)

Tous les fichiers sont en parquet dans `data/processed/` (copie sur S3), sauf les offres brutes, dans `data/raw/offres_raw/<source>.parquet`. **Ne jamais partager `data/cache/`** (cache HTTP). **Ne pas changer un schéma sans prévenir l'équipe et mettre à jour ce tableau ET `radar/schemas.py`** (vérification : `check_columns(df, "<nom>")`).

Données factices pour développer sans la collecte : `uv run python scripts/make_fake_data.py` (T5 ; recruteurs LBA ajoutés par T7). Les offres brutes factices ont, comme les vrais collecteurs, les colonnes propres à leur source (Adzuna : `region_requete`… ; LBA : `niveau_diplome`… — T19), tirées avec un générateur aléatoire à part. Elles produisent tous les fichiers ci-dessous ; le script refuse d'écraser des fichiers existants sans `--force`.

| Fichier | Produit par | Utilisé par | Colonnes clés |
|---|---|---|---|
| `data/raw/offres_raw/<source>.parquet` | collect/* | process | `source, offre_id, date_collecte, date_publication, titre, description, entreprise_nom, commune, code_postal, lat, lon, contrat_brut, code_rome, url, siret (si fourni)` — ces 15 colonnes en premier, dans cet ordre ; une source peut ajouter ses propres colonnes après (ex. Adzuna : `contrat_temps, categorie, salaire_min, salaire_max, salaire_predit, zone, requete, region_requete`) ; LBA : `partenaire, naf, naf_libelle, taille, adresse, niveau_diplome, nb_postes, statut, date_expiration, date_debut, duree_mois, teletravail, delegue_ecole` (si `delegue_ecole` est vrai, le SIRET est celui de l'école) |
| `data/raw/lbb.parquet` | collect/lbb (T28) | score | `siret, rome, domaine, lbb_potentiel, lbb_fort_potentiel, nom, naf, naf_libelle, commune, code_postal, departement, region, lat, lon, date_collecte` — une ligne par (établissement, métier) La Bonne Boîte ; `lbb_potentiel` = `hiring_potential` |
| `data/raw/lba_recruteurs.parquet` | collect/lba | score, app | `source, recruteur_id, date_collecte, siret, nom, raison_sociale, naf, naf_libelle, taille, adresse, code_postal, commune, lat, lon, site_web, opco, idcc, code_rome, url` — « recruteurs potentiels » LBA : entreprises **sans offre publiée** susceptibles d'embaucher des alternants (signal d'opportunité cachée) |
| `offres.parquet` | process | score, app | ci-dessus + `domaine: str` (clé de `domains.yaml` ou `autre`), `contrat: stage/alternance/emploi`, `siret_match, match_score, match_methode` ; en plus : `domaine_regle` (`rome_partiel+titre` / `rome` / `titre` / `aucune`), `contrat_regle` (`contrat_brut` / `titre` / `defaut`). `match_methode` : `siret_source` (SIRET donné par LBA, score 100), `siret_ecole_exclu` (offre déléguée à une école : SIRET retiré), `a_rapprocher` (à compléter par T21), puis les valeurs de T21 ; **après T21** (schéma `offres_rapprochees` dans `radar/schemas.py`, D7/D10) : `siren_match, match_confiance` (haute / moyenne), `match_distance_km, intermediaire` (plateformes / cabinets / intérim : pas de SIRET, voulu). `match_methode` ∈ exact, prefixe, sigle, flou, (…_loin), source, intermediaire, aucun |
| `entreprises.parquet` | collect/sirene, collect/bodacc | process, score, app | `siret, siren, nom, naf, naf_libelle, tranche_effectif, categorie, lat, lon, commune, ca_n, ca_n_1, procedure_collective: bool, lbb_proba` ; extras T20 : `nom_etablissement, annee_effectif, code_commune, code_postal, departement, siege, diffusion_partielle, qualite_xy, naf_section, naf_section_libelle, naf_division, effectif_min, effectif_max, effectif_estime, tranche_libelle, adresse, tranche_entreprise, tranche_entreprise_libelle, annee_effectif_entreprise` (T73 : tranche officielle de l'unité légale ; adresse vide si diffusion partielle ; effectif_estime = valeur centrale géométrique de la tranche, exposition du modèle). `ca_n, ca_n_1, lbb_proba, procedure_collective` = **manquants** (NA) tant que T22–T24 ne sont pas faites ; **BODACC (T23, D24)** : `procedure_type` (sauvegarde / redressement / liquidation / plan, vide sinon), `procedure_date`, `procedure_nature`, `procedure_url`, et `procedure_collective` rempli (True = alerte) |
| `scores.parquet` | score | app | **une ligne par (`siret`, `domaine`)** : composantes dans [0, 1] (`c_intensite, c_dynamisme, c_embauche…`) + `n_offres, n_offres_domaine, n_stage_domaine, n_alternance_domaine, intensite_post, intensite_ic_bas, intensite_ic_haut` ; **réel (T30)** : schéma `scores_reels` (+ `siren, couverture, prior_moyenne, besoin_attendu, n_*_domaine_siren, volume_suspect, c_embauche_source, c_dynamisme_disponible, lbb_potentiel`), domaine data seulement ; `c_embauche_source` ∈ {`la_bonne_boite`, `proxy_besoin_attendu`} (T28, D27), `intensite_*` en offres pour 100 salariés |
| `candidatures_simulees.parquet` | response/simulate | response/model | `siret, profil_id, domaine, contrat_vise, distance_km, <variables>, p_vraie, repondu: bool` — **données simulées** ; produit par `radar/response/simulate.py` (T35), règle dans `radar/response/params.yaml`, + `siren, ville, c_intensite, c_embauche, log10_effectif, distance_10km, alternance, a_offre_domaine, u_entreprise, donnees_simulees` |
| `p_reponse.parquet` | response/model | app | `siret, domaine, contrat_vise, p_reponse, contributions…` ; **réel (T36)** : schéma `p_reponse_modele` (+ `donnees_simulees`, `contrib_*`), à distance nulle ; distance ajoutée par l'app via `data/processed/modele_reponse.json` |

**Comptes (T48, D14)** : `data/app/radar.db` (SQLite, jamais dans Git ni sur S3) — tables `users(id, username, password_hash, created_at)`, `profils(user_id, data JSON, updated_at)` et `recherches(id, user_id, created_at, params JSON, n_resultats, top_resultats JSON)` (T49 : 50 max par compte, ajustements à moins de 2 min fusionnés) et `favoris(id, user_id, kind offre|entreprise, ref offre « source:offre_id » | siret, label, details JSON, note, candidate, created_at)` (T54, 500 max, unique par (user_id, kind, ref)). Rien n'y est écrit en mode anonyme.

Le score final **n'est pas stocké** : l'app le calcule à la volée, `score = Σ wⱼ · cⱼ`, avec les poids choisis par l'utilisateur. L'adéquation (distance, CV) et l'**opportunité cachée** dépendent de l'utilisateur (contrat visé) et sont calculées dans l'app : opportunité cachée = besoin dans le domaine (offres d'emploi) mais 0 offre du contrat visé (stage ou alternance).

## Modèle de score (détail)

**v1 (D33, en production)** : `radar/score/covariates.py`. k_i ~ BinNeg(μ_i E_i, φ) avec log μ_i = x_i·β (Poisson + offset log E, φ par moments), a posteriori Gamma(1/φ + k_i, 1/(φ μ_i) + E_i). Covariables dans `radar/score/features.py` : division NAF, taille, nb d'établissements, âge, modifications de capital (BODACC), densité d'entreprises data à 3 km, catégorie, ESS, mission. Repli automatique sur **v0 (D13)** (`radar/score/intensity.py`, a priori par secteur seulement) si les caractéristiques manquent ; `score_version` dans `scores.parquet`.
- **Composantes** dans [0, 1] par rangs centiles : `c_intensite` (λ a posteriori), `c_embauche` (La Bonne Boîte d'abord, sinon besoin attendu de l'établissement, D27), `c_dynamisme` (neutre 0,5 en attendant T22).
- **Évaluation** : `scripts/eval_score.py` → `docs/EVAL_SCORE.md` (validation temporelle, besoin caché, AUC à taille comparable).

## Explication des recommandations (T32, D29)

`radar/explain.py` → colonne `explication` ajoutée par `rank_spontaneous` (1 000 premières lignes) : « Recommandée car <opportunité cachée> ; <raisons classées par apport au score> » + mise en garde si la région n'est pas collectée. Lue par la fiche (`app/fiche_ui.py`, T43) et le popup orange (`app/streamlit_app.py`).

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
