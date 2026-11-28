# Journal — Celia

> Une entrée par session ou par tâche terminée, **la plus récente en haut**. Seule Celia écrit dedans.

---

## 2026-11-28 — Tâche T89 : fiche plus claire (T92 ajoutée)

**Fait :**
- En-tête avec pastilles, ligne de boutons, onglets Résumé / Offres / (Sites) / Infos, d'après un croquis validé. Présentation seulement.
- Ajouté au tableau : adresses des sites web à retravailler (T92).

**Résultats / chiffres clés :**
- Vérifié avec les vraies données (site, entreprise, entreprise en redressement). 384 tests OK.

---

## 2026-11-27 — Tâche T88 : « Comment la contacter ? » (T89 à T91 ajoutées)

**Fait :**
- Trois boutons de recherche pré-remplie dans les deux fiches (`contact_searches`).
- Constat : le champ `site_web` de La bonne alternance est vide (0 sur 382 180) → pas de lien direct vers les sites.
- Ajouté au tableau : T89 (fiche plus claire), T90 (rappels de relance), T91 (export, facultatif).

**Résultats / chiffres clés :**
- 384 tests OK.

---

## 2026-11-27 — Tâche T84 : recherches enregistrées (D43)

**Fait :**
- Table `recherches_enregistrees` (20 max, sans doublon), `app/recherches.py` (bouton Explorer, liste Mon espace, mode sans compte repris à la connexion).
- Historique automatique retiré de l'app (décision B) ; compteur de l'administration rebranché ; tests de l'ancien historique remplacés par `tests/test_recherches_enregistrees.py`.

**Résultats / chiffres clés :**
- Parcours vérifié dans l'app avec les vraies données (enregistrer, relancer, sans compte). 382 tests OK après le développement.

**Problèmes / points d'attention pour l'équipe :**
- Les lignes de l'ancien historique restent dans les bases existantes (non affichées) : à effacer si l'équipe le souhaite.

---

## 2026-11-27 — Tâche T85 : Mon espace repensé

**Fait :**
- Page en résumé chiffré + 4 onglets ; connexion en deux colonnes ; pastilles de statut. Présentation seulement.
- Fusion avec la T83 d'Emma (CV et compétences saisies à la main) : sa fonction `_profile_section` et `cv_and_skills` reprises à l'identique dans l'onglet « Mon profil ». Étiquette de ma tâche renumérotée T85 (T83 prise par Emma).

**Résultats / chiffres clés :**
- 380 tests OK.

---

## 2026-11-27 — Tâche T82 : Mes candidatures

**Fait :**
- Colonne `statut` dans la table `favoris` (migration automatique), `CANDIDATURE_STATUTS`, `update_favorite(statut=...)`.
- Mon espace : onglet « Mes candidatures » (favoris cochés « Candidaté », statut modifiable). Textes de création de compte simplifiés (liste des règles du mot de passe) ; marge du haut rendue à Streamlit (la page commence sous la barre).

**Résultats / chiffres clés :**
- Vérifié dans l'app avec les vraies données ; tests comptes / favoris OK.

---

## 2026-11-27 — Tâche T76 : candidature spontanée dans les fiches

**Fait :**
- `offer_signal` sorti du popup de la carte (même texte) et affiché dans la fiche site (« Candidature spontanée · … »).
- Explorer garde les candidatures de la recherche en cours (`_candidatures`, `_candidatures_ctx`) : une fiche site ouverte depuis la recherche ou la liste des sites retrouve palier, score, distance, explication.
- Fiche entreprise : bloc « Candidature spontanée » (sites dans la recherche, le mieux classé, les suivants, bouton vers sa fiche, famille ; messages si aucun site ou pas de ville).

**Fichiers touchés :**
- `app/carte.py`, `app/fiche_ui.py`, `app/vues/explorer.py`, `tests/test_fiche.py`, `docs/*`

**Résultats / chiffres clés :**
- Orange autour de Rennes : 15 sites dans la recherche, le mieux classé « Cible prioritaire ». 349 tests OK.
- Vérifié ensuite avec les **vraies données** de Mathis : il a fallu corriger le chargement des offres (l'app ne lisait que les offres brutes, absentes de la liste du README ; repli sur `offres.parquet`). Rennes, stage : 3 714 entreprises (4 349 sites), 8 offres, 435 cibles prioritaires ; fiche d'Infotel Conseil complète (signal, explication, chance de réponse).

---

## 2026-11-27 — Tâche T73 : effectifs par site et par entreprise

**Fait :**
- Extraction SIRENE : tranche officielle de l'entreprise (`trancheEffectifsUniteLegale`, année) → `tranche_entreprise`, `tranche_entreprise_libelle`, `annee_effectif_entreprise` ; réextraction + BODACC réappliqué.
- `tranche_display` : « entre 2 000 et 4 999 salariés » pour l'affichage (TRANCHE_LIBELLES inchangé car utilisé par l'explication de Mathis).
- Deux colonnes « Taille entreprise » (officielle) et « Taille site » dans la recherche et la liste des candidatures (vide sur la ligne « toute l'entreprise » et quand l'info manque) ; fiche entreprise : taille officielle ; total estimé abandonné à la demande de Celia (fausse précision : 44 000 à 89 000 pour Orange).

**Fichiers touchés :**
- `radar/collect/sirene.py`, `radar/fiche.py`, `radar/recherche.py`, `app/fiche_ui.py`, `app/vues/explorer.py`, `app/vues/entreprises.py`, `docs/*`

**Résultats / chiffres clés :**
- Orange : « 10 000 salariés et plus » (SIRENE 2024), 524 sites ; Orange Lyon « entre 1 000 et 1 999 salariés ». Tranche entreprise remplie à 100 %. 348 tests OK.

**Problèmes / points d'attention pour l'équipe :**
- Relancer `extract_sirene.py` puis `collect_bodacc.py` (ou `build_all.py --sirene`).
- Bug trouvé en vérifiant : Explorer plante avec les données factices depuis T26 (colonnes `*_siren` absentes des scores factices) → **T75**, signalé à Maxence (numéro T74 déjà pris par Emma).

---

## 2026-11-27 — Tâche T72 : nom cliquable ; T73 ajoutée

**Fait :**
- Liste des candidatures spontanées, résultats de recherche et liste des sites de la fiche entreprise : le nom est en bleu souligné ; un clic sur le nom ouvre la fiche (sélection d'une cellule), plus de case à cocher. Tableau, colonnes, tri et recherche inchangés (demande de Celia).
- Bug corrigé (présent depuis T57) : le clic sur un site faisait `st.rerun(scope="fragment")`, qui plante si toute la page se relance ; remplacé par un rappel `on_select`.
- T73 ajoutée (effectifs : tranche par site plus claire, tranche officielle de l'entreprise + total estimé à partir des sites), à faire plus tard.

**Fichiers touchés :**
- `app/vues/explorer.py`, `app/vues/entreprises.py`, `app/style.py`, `docs/*`

**Résultats / chiffres clés :**
- Clic simulé : sur « Lieu » rien, sur le nom la fiche s'ouvre (Explorer et Entreprises). 344 tests OK.

---

## 2026-11-27 — Tâche T71 : liste qui plantait sur une grande ville

**Fait :**
- Liste « Candidatures spontanées » limitée aux 500 premières lignes affichées et colorées (`MAX_LIST_ROWS`), avec une mention ; la sélection d'une ligne ouvre toujours la bonne fiche.
- Reproduit avec des scores factices autour de Paris (60 666 établissements, 20 km) : l'ancienne version plantait (Styler pandas : 472 440 cellules > 262 144), la nouvelle affiche 500 lignes sans erreur.
- Maxence prévenu dans `TACHES.md` (son code de T65).

**Fichiers touchés :**
- `app/vues/explorer.py`, `docs/TACHES.md`, `docs/GUIDE.md`

**Résultats / chiffres clés :**
- 343 tests OK.

---

## 2026-11-27 — Tâche T70 : apparence plus vivante (hors fiche)

**Fait :**
- `app/style.py` : CSS commun (fond, cartes arrondies avec ombre, onglets), bandeau d'en-tête, tuiles de chiffres, pastilles.
- Explorer : bandeau + carte de recherche posée dessus ; « Comment ça marche » en 3 cartes ; tuiles (entreprises à démarcher, offres, cibles prioritaires, en difficulté) ; « Les meilleures cibles » (4 cartes avec palier T65 et « Voir la fiche »).
- Icônes Material : navigation, Filtres, onglets, boutons de Mon espace. Bandeau compact sur Entreprises et Mon espace.

**Fichiers touchés :**
- `app/style.py`, `app/streamlit_app.py`, `app/vues/*`, `app/compte.py`, `tests/test_compte_ui.py`, `docs/*`

**Résultats / chiffres clés :**
- Autour de Rennes (scores factices) : tuiles 3 755 / 17 / 444 / 54. 320 tests OK.

**Problèmes / points d'attention pour l'équipe :**
- Les sélecteurs CSS internes de Streamlit changent d'une version à l'autre : on ne style que nos blocs à clé (`st-key-…`).
- Vérification visuelle faite par Celia dans l'aperçu (pas de navigateur sans affichage utilisable sur le pod).
- La fiche n'est pas retouchée (T67 d'Emma en cours dessus).

---

## 2026-11-27 — Tâche T64 : « Chance de réponse » (D31)

**Fait :**
- « P(réponse) simulée » → « Chance de réponse » (liste, popup de la carte, fiche, classement) ; colonne toujours affichée quand le modèle couvre le contrat et le domaine.
- Choix de Celia : plus de bandeau « Démonstration » ni de « (démo) » à l'écran ; la mention « réponses simulées » reste en info-bulle (`CHANCE_HELP`) et sera dite au pitch. D31 précise D6 / D23 sur l'affichage.

**Fichiers touchés :**
- `app/commun.py`, `app/vues/explorer.py`, `app/fiche_ui.py`, `app/carte.py`, `docs/*`

**Résultats / chiffres clés :**
- Vérifié avec une chance de réponse simulée de 34 % : colonne visible avec le classement par score, aucun bandeau. 305 tests OK.

**Problèmes / points d'attention pour l'équipe :**
- Au pitch, dire que les chances de réponse viennent de réponses simulées (D6, D31).

---

## 2026-11-27 — Tâche T57 : entreprise (SIREN) et sites (SIRET)

**Fait :**
- `radar/fiche.py` : `company_sites`, `company_summary` ; `radar/recherche.py` : `_n_sites`, `with_companies`.
- Fiche entreprise dans la même fenêtre que la fiche site (`_fiche_nav`), avec sites cliquables et boutons retour ; favori « toute l'entreprise ».
- Page Entreprises : l'entreprise entière d'abord, puis les sites (choix de Celia).
- Candidatures spontanées : colonne « Autres sites », option « Une ligne par entreprise », phrase « N entreprises (M sites) ».

**Fichiers touchés :**
- `radar/fiche.py`, `radar/recherche.py`, `app/fiche_ui.py`, `app/commun.py`, `app/vues/explorer.py`, `app/vues/entreprises.py`, `app/vues/mon_espace.py`, tests, `docs/*`

**Résultats / chiffres clés :**
- Orange (SIREN 380 129 866) : 524 sites, ≈ 62 690 salariés. Recherche « orange » : 5 entreprises puis les sites. Autour de Rennes (scores factices) : 3 755 entreprises pour 4 438 sites. 305 tests OK.

**Problèmes / points d'attention pour l'équipe :**
- Filiales d'un groupe non reliées (L24) : à traiter avec T26.

---

## 2026-11-27 — Tâche T54 : favoris

**Fait :**
- `radar/accounts.py` : table `favoris` (offres et entreprises, note, case « candidaté », 500 max, suppression avec le compte).
- `app/favoris.py` : étoile (fiche), cases ★ (liste des offres), colonne ★ (candidatures), bandeau des favoris temporaires.
- Choix avec Celia : en anonyme, favoris temporaires (rien sur le disque), **enregistrés automatiquement** à la connexion ou à la création du compte (`compte._flush_temp_favorites`).
- Mon espace : « Mes favoris » (voir la fiche, voir l'offre, « n'est plus en ligne », case « Candidaté », note, retirer).

**Fichiers touchés :**
- `radar/accounts.py`, `app/favoris.py`, `app/compte.py`, `app/fiche_ui.py`, `app/vues/explorer.py`, `app/vues/mon_espace.py`, `app/streamlit_app.py`, `tests/test_accounts.py`, `tests/test_favoris.py`, `CLAUDE.md`, `docs/*`

**Résultats / chiffres clés :**
- Parcours vérifié : 2 favoris temporaires → création du compte → enregistrés ; note et case sauvegardées ; retrait. 293 tests OK.

**Prochaine étape :**
- Statuts de candidature (à contacter / envoyée / relancée / réponse) si l'équipe le souhaite.

---

## 2026-11-27 — T56 interface en 3 pages (D30) et T38 La Bonne Boîte dans la fiche

**Fait :**
- Refonte de l'interface avec Celia : navigation en haut, 3 pages (Explorer, Entreprises, Mon espace), recherche en haut + panneau « Filtres », phrase de résultat, fiche en fenêtre au clic, textes sans jargon, thème sobre.
- `radar/recherche.py` : recherche d'entreprises sur ~406 000 établissements (présélection par début de mot, note mot par mot ; 0,05–0,4 s ; « spora steira » → Sopra Steria ; sigles ; SIREN/SIRET).
- Intégration des 15 commits de l'équipe faits pendant la refonte : suggesteur de ville (T55), La Bonne Boîte (T29), explication (T32) ; `app/carte.py` vérifié identique à la carte de `main`.
- T38 : signal La Bonne Boîte dans la fiche.

**Fichiers touchés :**
- `app/streamlit_app.py`, `app/commun.py`, `app/carte.py`, `app/vues/*`, `app/fiche_ui.py`, `app/compte.py`, `radar/recherche.py`, `radar/fiche.py`, `.streamlit/config.toml`, tests, `CLAUDE.md`, `docs/*`

**Résultats / chiffres clés :**
- 286 tests OK.

**Problèmes / points d'attention pour l'équipe :**
- La carte et le popup sont dans `app/carte.py` ; les pages dans `app/vues/`. Nouvelle consigne des réglages dans `CLAUDE.md`.

---

## 2026-11-27 — Tâche T43 : fiche entreprise

**Fait :**
- `radar/fiche.py` : `load_company`, `company_offers` (par SIREN, sans intermédiaires), `bodacc_history`, `evidence` (niveau de preuve), `links`.
- `app/fiche_ui.py` + appel dans `app/streamlit_app.py` : panneau « 🔎 Fiche entreprise » sous la liste orange (identité + alerte, pourquoi recommandée + décomposition du score, besoin dans le domaine + intervalle crédible à 90 %, offres récentes, historique BODACC, coordonnées et liens).
- Coordination avec T32 (@mathis) notée dans `TACHES.md` : la fiche affiche sa colonne `explication`, il garde le popup.
- Sélecteur de toute la liste (5 000 max, recherche par nom) : les entreprises en procédure, pénalisées, sont classées loin.

**Fichiers touchés :**
- `radar/fiche.py`, `app/fiche_ui.py`, `app/streamlit_app.py`, `tests/test_fiche.py`, `docs/*`

**Résultats / chiffres clés :**
- Vérifié dans l'app (scores factices autour de Rennes) : entreprise saine, en redressement (×0,40, 1 annonce) et en liquidation (×0,05, 3 annonces) ; aucune erreur.
- 6 tests ; suite complète : 255 tests OK.

**Prochaine étape :**
- Quand T32 sera poussée : vérifier que la phrase s'affiche dans la fiche. Avec T22 : ajouter le chiffre d'affaires.

---

## 2026-11-27 — Tâche T23 : BODACC, entreprises en difficulté (D24)

**Fait :**
- `radar/collect/bodacc.py` : export BODACC des 2 dernières années (procédures collectives), classement des natures de jugement, dernier événement qui change la situation par SIREN, enrichissement de `entreprises.parquet`. Script `scripts/collect_bodacc.py`, étape « 1 bis » dans `build_all.py`.
- `radar/procedures.py` : pénalité selon la situation et le contrat visé (`PENALTIES`), alertes 🟡/🟠/🔴.
- `radar/spontaneous.py` : colonnes BODACC chargées, `apply_procedures` dans `rank_spontaneous` (paramètre `show_liquidation`).
- App : case « Afficher aussi les entreprises en liquidation » (dans le profil), colonne « Situation », alerte + lien BODACC dans la fiche.
- Choix discuté avec l'équipe : pénaliser et signaler plutôt que supprimer (D24).

**Fichiers touchés :**
- `radar/collect/bodacc.py`, `radar/procedures.py`, `radar/spontaneous.py`, `scripts/collect_bodacc.py`, `scripts/build_all.py`, `app/streamlit_app.py`, `tests/test_bodacc.py`, `CLAUDE.md`, `docs/*`

**Résultats / chiffres clés :**
- 404 778 annonces (47 Mo, ~1 min) → 205 047 SIREN ; 11 124 établissements en alerte sur 406 266 (2,7 %) : 6 130 liquidations, 2 449 redressements, 2 046 plans, 499 sauvegardes.
- Autour de Rennes (20 km, alternance, scores factices) : 54 alertes visibles, 58 liquidations masquées.
- 28 tests T23 ; suite complète : 249 tests OK.

**Problèmes / points d'attention pour l'équipe :**
- Relancer `scripts/build_all.py` (ou `collect_bodacc.py`) pour avoir les colonnes BODACC dans son `entreprises.parquet`.
- Coefficients de pénalité choisis à dire d'expert (L23) : à discuter si besoin, réglables dans `radar/procedures.py`.

---

## 2026-11-27 — Sécurité des mots de passe (suite de T48, D16)

**Fait :**
- `radar/accounts.py` : `password_problems` (12 caractères min., 3 types, liste noire, identifiant interdit), blocage par compte en base (5 échecs → 15 min, `AccountLocked`), mise à jour automatique des anciennes bases.
- `app/compte.py` : règles affichées sous le champ mot de passe, heure de déblocage affichée ; le compteur par onglet est remplacé par le blocage en base.
- `docs/SECURITE.md` : tout ce qu'on fait pour les mots de passe, et ce qui manque (référencé dans `CLAUDE.md`). D16, L19.

**Fichiers touchés :**
- `radar/accounts.py`, `app/compte.py`, `tests/test_accounts.py`, `tests/test_compte_ui.py`, `docs/SECURITE.md`, `CLAUDE.md`, `docs/*`

**Résultats / chiffres clés :**
- 46 tests comptes (dont 17 sur la sécurité, et un test qui vérifie que le blocage résiste au rechargement de la page).

**Problèmes / points d'attention pour l'équipe :**
- Les mots de passe de test doivent maintenant respecter les règles (ex. `Radar-Demo-2026`).
- Les comptes créés avant D16 gardent leur ancien mot de passe.

---

## 2026-11-27 — Tâche T49 : historique des recherches

**Fait :**
- `radar/accounts.py` : table `recherches`, `log_search` / `list_searches` / `clear_searches`. Streamlit relance la page à chaque réglage → les changements à moins de 2 min de la dernière recherche la mettent à jour (un cran de curseur ≠ une recherche), recherche identique non dupliquée, 50 max par compte, suppression avec le compte.
- `app/compte.py` : `search_history(...)`, appelée après le calcul des résultats. Anonyme : ne fait rien. Connecté : enregistre et affiche « 🕘 Mes recherches » (date, résumé lisible, nombre de résultats, 3 premières entreprises), « ↻ Relancer » (rappel `on_click`, pour modifier les widgets avant qu'ils soient redessinés) et « Effacer mon historique ».
- `app/streamlit_app.py` : `PROFILE_LABELS` (libellés du résumé) et appel de `search_history`.

**Fichiers touchés :**
- `radar/accounts.py`, `app/compte.py`, `app/streamlit_app.py`, `tests/test_accounts.py`, `tests/test_compte_ui.py`, `docs/*`

**Résultats / chiffres clés :**
- 29 tests comptes + historique (dont l'app complète en mode connecté) ; suite complète : 143 tests OK.

**Problèmes / points d'attention pour l'équipe :**
- T40/T41/T42 : nouveau réglage = `key` + entrée dans `PROFILE_KEYS` **et** un libellé dans `PROFILE_LABELS`.
- « Effacer mon historique » garde la recherche en cours (elle est réenregistrée aussitôt).

**Prochaine étape :**
- Avec T40 : passer les SIRET des entreprises orange dans `top=`.

---

## 2026-11-27 — Tâche T48 : connexion facultative + profil

**Fait :**
- `radar/accounts.py` : comptes et profils en SQLite (`data/app/radar.db`), mots de passe scrypt (bibliothèque standard), suppression en cascade.
- `app/compte.py` : bloc de la barre latérale. Mode démo anonyme par défaut ; connexion / création de compte (les réglages actuels deviennent le profil) ; enregistrer, se déconnecter, supprimer son compte (case à cocher). 5 essais de connexion par session.
- `app/streamlit_app.py` : une `key` par réglage, `PROFILE_KEYS`, appel du bloc compte. Valeurs par défaut via `session_state.setdefault`.
- D14 mise à jour (scrypt au lieu de `streamlit-authenticator`), L17–L18 dans `LIMITES.md`.

**Fichiers touchés :**
- `radar/accounts.py`, `app/compte.py`, `app/streamlit_app.py`, `tests/test_accounts.py`, `tests/test_compte_ui.py`, `docs/*`

**Résultats / chiffres clés :**
- 19 tests T48 (13 module, 6 parcours Streamlit avec AppTest, dont l'app complète sur offres factices) ; suite complète : 133 tests OK.

**Problèmes / points d'attention pour l'équipe :**
- T40/T41/T42 : chaque nouveau réglage doit avoir une `key` et figurer dans `PROFILE_KEYS`, sinon il n'est pas enregistré dans le profil.
- Les données factices font planter l'app (format de `date_collecte`) → tâche T19.

**Prochaine étape :**
- T49 (historique des recherches) : ajouter une table `recherches` dans `radar/accounts.py` et une liste « Mes recherches » dans `app/compte.py`.

---

## 2026-11-27 — Fusion des deux versions de T20 (avec Mathis)

**Fait :**
- Mon push étant bloqué, Mathis a aussi réalisé T20. Fusion au `git pull` : base = version de Mathis (utilisée par T21), avec mes ajouts : nom des entrepreneurs individuels, `tranche_libelle`, `adresse` (masquée si diffusion partielle), `--dep`, tests sur les tranches et la requête. Décision D11.
- Supprimé : `radar/naf_rev2.csv` et son exception `.gitignore` (doublon du parquet NAF de Mathis), `python -m radar.collect.sirene` (remplacé par `scripts/extract_sirene.py`).

**Fichiers touchés :**
- `radar/collect/sirene.py`, `scripts/extract_sirene.py`, `tests/test_sirene.py`, `.gitignore`, `CLAUDE.md`, `docs/*`

**Résultats / chiffres clés :**
- Test sur le 35 : 7 514 établissements, 0 sans nom, 99,9 % géolocalisés, 99,8 % avec adresse.

**Problèmes / points d'attention pour l'équipe :**
- Régénérer `entreprises.parquet` avec `uv run python scripts/extract_sirene.py` pour avoir `tranche_libelle` et `adresse`.

---

## 2026-11-27 — Tâche T20 : référentiel SIRENE France

**Fait :**
- `radar/collect/sirene.py` : DuckDB lit à distance les 3 stocks parquet SIRENE (établissements, unités légales, géolocalisation) et écrit `data/processed/entreprises.parquet`, conforme à `radar/schemas.py` (colonnes du contrat + colonnes utiles en plus, voir `ARCHITECTURE.md`).
- `radar/naf_rev2.csv` : libellés NAF rév. 2 (INSEE), avec une exception dans le `.gitignore`.
- `tests/test_sirene.py` : table NAF, tranches, requête valide (sans réseau), contrat respecté si le fichier existe.
- Décision D11 (voir l'entrée de fusion ci-dessus).

**Fichiers touchés :**
- `radar/collect/sirene.py`, `radar/naf_rev2.csv`, `tests/test_sirene.py`, `.gitignore`, `CLAUDE.md` (une commande), `docs/*`

**Résultats / chiffres clés :**
- 406 266 établissements actifs ≥ 10 salariés, 278 950 entreprises, 101 départements ; 99,7 % géolocalisés ; 0 % sans nom ; 100 % avec libellé NAF ; 19 Mo ; 39 s.
- Effectifs : tous de 2024. Catégories : 245 k PME, 96 k ETI, 61 k GE.
- Ille-et-Vilaine (35) : 7 514 établissements.

**Problèmes / points d'attention pour l'équipe :**
- Chacun peut régénérer le fichier : `uv run python scripts/extract_sirene.py` (option `--dep 35` pour tester).
- `ca_n`, `ca_n_1`, `lbb_proba` sont vides et `procedure_collective` vaut `False` : à remplir par T22, T24 et T23.
- `.gitignore` : ajout de l'exception `!radar/naf_rev2.csv`.
- ⚠️ `uv run ruff format .` reformate aussi les blocs Python **dans les fichiers Markdown** (dont les journaux des autres) : vérifier son `git diff` avant de committer.

**Prochaine étape :**
- T21 (rapprochement nom + commune → SIRET) peut s'appuyer sur `nom`, `nom_entreprise`, `sigle`, `code_postal`, `code_commune`.
