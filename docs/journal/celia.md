# Journal — Celia

> Une entrée par session ou par tâche terminée, **la plus récente en haut**. Seule Celia écrit dedans.

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
