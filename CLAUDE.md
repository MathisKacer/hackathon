# CLAUDE.md — Hackathon ENSAI (M2)

Ce fichier est lu par **toutes** les sessions Claude Code de l'équipe. Plusieurs personnes travaillent en parallèle sur le même dépôt, chacune avec sa propre session : la coordination passe par les fichiers de `docs/`, pas par la mémoire de Claude.

## Le projet en bref

**Radar** : trouver les entreprises proches d'un étudiant qui ont un besoin data mais pas d'offre de stage visible, pour des candidatures spontanées. Score explicable (bayésien empirique), données ouvertes uniquement. Détails dans `docs/PROJET.md`.

- **Échelle :** France entière ; domaine paramétrable (data par défaut) ; stage, alternance et emploi
- **Livrable final :** application Streamlit + slides de pitch
- **Durée :** hackathon de **24 h** → jalons et gel des fonctionnalités dans `docs/TACHES.md`. Toujours privilégier ce qui fait avancer le prochain jalon.
- **Équipe :** Mathis, Celia, Maxence, Emma

## Où se trouve quoi

| Fichier | Rôle | Qui écrit |
|---|---|---|
| `docs/PROJET.md` | Pitch, objectifs, livrables, critères du jury | Toute l'équipe (rarement modifié) |
| `docs/MODELE_REPONSE.md` | Rapport du modèle de réponse (réponses simulées) : AUC, calibration, paramètres retrouvés — **généré**, ne pas éditer | `scripts/build_response.py` |
| `docs/LIMITES.md` | Limites connues : impact, réglable ou non, tâche associée, ce qu'il faut en dire au pitch | Quiconque découvre ou lève une limite |
| `docs/SECURITE.md` | Sécurité des comptes : règles des mots de passe, stockage, blocage, ce qui manque | Quiconque touche aux comptes |
| `docs/SOURCES.md` | Inventaire des API et données (accès, quotas, statut testé) | Quiconque teste une source |
| `docs/ARCHITECTURE.md` | Structure technique : modules, données, flux, conventions | Quiconque change la structure |
| `docs/TACHES.md` | Tableau des tâches (à faire / en cours / fait) avec responsable | Tout le monde, en continu |
| `docs/DECISIONS.md` | Journal des décisions importantes et de leur justification | Quiconque tranche un choix |
| `docs/journal/<prenom>.md` | Journal personnel des avancées, une entrée par session | **Uniquement son propriétaire** |

## Rituel de chaque session Claude

**Au démarrage :**
1. `git pull --rebase` pour récupérer le travail des autres.
2. Lire `docs/TACHES.md`, `docs/ARCHITECTURE.md` et les dernières entrées des journaux (`docs/journal/`).
3. Demander à l'utilisateur son prénom s'il n'est pas connu, et quelle tâche il prend. La passer en « En cours » dans `docs/TACHES.md` avec son nom **et committer tout de suite** pour que les autres le voient.

**Pendant le travail :**
- Rester dans le périmètre de la tâche prise. Ne pas refactorer ni reformater du code qui appartient à une autre tâche en cours.
- Si un fichier partagé (config, utilitaires communs, schéma de données) doit changer, le signaler à l'utilisateur pour qu'il prévienne l'équipe.
- Tout choix structurant (lib, format de données, découpage) → une entrée dans `docs/DECISIONS.md`.

**À la fin d'une tâche ou de la session :**
1. Ajouter une entrée dans `docs/journal/<prenom>.md` (format dans `docs/journal/_MODELE.md`).
2. Mettre à jour `docs/TACHES.md` (passer en « Fait », ajouter les nouvelles tâches découvertes).
3. Mettre à jour `docs/ARCHITECTURE.md` si la structure a changé.
4. Committer et pousser (voir conventions Git).

## Conventions Git (éviter les conflits)

- Commits petits et fréquents ; `git pull --rebase` avant chaque `git push`.
- Branches courtes : `<prenom>/<sujet>` (ex. `mathis/nettoyage-donnees`), fusionnées dans `main` dès que ça marche. Les mises à jour de `docs/` peuvent aller directement sur `main`.
- Messages de commit en français, préfixés : `feat:`, `fix:`, `data:`, `docs:`, `refactor:`.
- Conflit sur un fichier de `docs/` : garder **les deux** versions (ce sont des listes), jamais écraser le travail d'un autre.
- Chacun n'écrit que dans **son** journal → zéro conflit sur `docs/journal/`.

## Règles de sécurité / données

- **Clés d'API** : `cp .env.example .env`, puis remplir. Le `.env` est **local à chaque pod Onyxia** (non versionné) : chaque membre crée le sien, et les clés se partagent par message privé, jamais via Git. Claude ne doit jamais afficher, journaliser ni committer le contenu du `.env`.
- **Ne jamais committer de données** ni de secrets : jeux de données dans `data/` (ignoré par Git) ou sur le stockage S3 Onyxia/SSP Cloud ; identifiants dans des variables d'environnement ou `.env` (ignoré).
- **Partager des données avec l'équipe** (y compris ceux qui ne sont pas sur Onyxia) : depuis un service Onyxia, `python3 scripts/share_s3.py data/<fichier>` dépose le fichier dans l'espace S3 **privé** et affiche une commande `curl` avec un lien temporaire (24 h). Envoyer cette commande en **message privé**. ⚠️ Le dépôt GitHub est **public** : jamais de données dedans, ni dans le dossier public `diffusion/` de S3 (les offres Adzuna ne doivent pas être redistribuées publiquement).
- Ne pas committer de notebooks avec des sorties volumineuses (vider les sorties avant commit).

## Stack et commandes

Python ≥ 3.11, dépendances gérées avec **uv** (`pyproject.toml` + `uv.lock` versionnés). Package `radar/`, app dans `app/`.

```bash
uv sync                                   # installer / mettre à jour l'environnement (.venv)
uv add <paquet>                           # ajouter une dépendance (commit pyproject.toml + uv.lock)
uv run python scripts/make_fake_data.py  # données FACTICES dans data/ (T5) pour lancer l'app sans la collecte
uv run python scripts/classify_offres.py # offres brutes → offres.parquet (domaine, contrat) (T13)
uv run python scripts/extract_sirene.py  # VRAI référentiel entreprises SIRENE (T20, ~2 min ; --dep 35 pour tester) → data/processed/entreprises.parquet
uv run python scripts/build_all.py        # reconstruire entreprises → offres → scores (~1 min)
uv run streamlit run app/streamlit_app.py # lancer l'app (port 8501)
uv run pytest -q                          # tests
uv run ruff format . && uv run ruff check --fix .   # formatage + lint, avant chaque commit
```

- Voir l'app depuis Onyxia (VS Code) : ouvrir `<URL de ton service>/proxy/8501/`.
- Chemins et clés : toujours via `from radar.config import PATHS, FILES, settings` ; jamais de chemin en dur ni de `os.getenv` dispersé.
- Appels HTTP : passer par un cache disque dans `PATHS.cache` (quota Adzuna ~250 appels/jour).

## Comptes et réglages de l'app (T48, T49, D14) — à respecter dans `app/streamlit_app.py`

L'app a un **mode démo anonyme** (par défaut, rien n'est enregistré) et une **connexion facultative** qui enregistre le profil (= les réglages de recherche) et l'historique des recherches. Pour que ça continue de marcher, **tout nouveau réglage de recherche** (T40, T41, T42…) doit :
1. avoir une `key` (ex. `st.slider(..., key="rayon_km")`) ;
2. être ajouté à `PROFILE_KEYS` avec ses options permises (`None` = valeur libre), sinon il n'est pas enregistré dans le profil ;
3. avoir un libellé dans `PROFILE_LABELS` (affiché dans « Mes recherches ») ;
4. prendre sa valeur par défaut avec `st.session_state.setdefault("rayon_km", 20)`, **pas** avec `value=` (sinon Streamlit avertit quand un profil la remplace) ;
5. être créé **après** `account_sidebar(PROFILE_KEYS)` dans la barre latérale.

Quand la couche orange (T40) existe : passer les SIRET des premières entreprises dans `top=` de `search_history(...)`. Code : `radar/accounts.py` (base SQLite `data/app/radar.db`, hors Git) et `app/compte.py` ; tests : `tests/test_accounts.py`, `tests/test_compte_ui.py`. **Sécurité des mots de passe** (règles, hachage, blocage) : `docs/SECURITE.md`, à mettre à jour si on y touche.

## Style de réponse attendu de Claude

- Répondre en français.
- Code et noms de variables en anglais ou français, mais **cohérents** avec l'existant (voir `docs/ARCHITECTURE.md` › Conventions).
- C'est un hackathon : privilégier ce qui marche et se démontre vite, mais garder le code lisible pour les coéquipiers.
