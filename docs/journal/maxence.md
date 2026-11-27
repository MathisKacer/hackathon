# Journal — Maxence

> Une entrée par session ou par tâche terminée, **la plus récente en haut**. Seul son propriétaire écrit dedans.

---

## 2026-11-27 — T41 : filtres domaine, contrat, taille, secteur

**Fait :**
- **Domaine** : la liste vient de `radar/domains.yaml` (data, informatique, finance, marketing, RH ; un domaine ajouté par T9 apparaîtra tout seul). Les offres 🔵 sont classées dans l'app par le même classifieur que T13 (code ROME + titre) au lieu du filtre « data » v0 ; le score 🟠 est celui du domaine choisi. Le bouton « Seulement les offres data » devient « Seulement les offres du domaine ».
- **Contrat** : déjà là (T40), inchangé.
- **Taille** (4 tranches : 10–49, 50–249, 250–999, 1 000 et plus) et **secteur** (21 sections NAF) : choix multiples dans un bloc « Entreprises 🟠 » de la barre latérale, appliqués à la couche orange. Nouveau module `radar/filters.py`.
- Consignes comptes respectées : clés `tailles` / `secteurs` dans `PROFILE_KEYS` et `PROFILE_LABELS`, créées après `account_sidebar`.
- Décision **D20**, limite **L20** (taille/secteur ne filtrent pas les offres bleues).

**Fichiers touchés :**
- `radar/filters.py` (nouveau), `tests/test_filters.py` (nouveau, 7 tests), `radar/spontaneous.py` (colonnes `naf`, `naf_section` lues), `app/streamlit_app.py`, `docs/DECISIONS.md`, `docs/LIMITES.md`, `docs/ARCHITECTURE.md`, `docs/TACHES.md`

**Résultats / chiffres clés :**
- 210 tests OK, ruff OK. Parcours vérifié avec AppTest (Rennes, 20 km, données factices) : 236 entreprises 🟠 → 45 en 50–249 salariés → 8 en plus dans le secteur J ; domaine « finance » : 6 offres 🔵 et 11 entreprises 🟠.

**Problèmes / points d'attention pour l'équipe :**
- Les profils enregistrés avec l'ancien domaine « Data » retombent sur le domaine par défaut (data) : rien à faire.
- Pour les offres 🔵, le domaine est recalculé dans l'app (les offres brutes, pas `offres.parquet`) : si T13 change de classifieur, l'app suit automatiquement puisqu'elle appelle `radar.domains.classify`.

**Prochaine étape :**
- T42 (curseurs de poids), T51 (recruteurs LBA dans la couche orange).

---

## 2026-11-27 — T40 : couche orange « Candidature spontanée »

**Fait :**
- `radar/geocode.py` : adresse → lat/lon via la Géoplateforme (IGN, sans clé), cache disque dans `PATHS.cache` ; renvoie None si introuvable / hors ligne.
- `radar/spontaneous.py` : `load_nearby` (DuckDB sur le rectangle du rayon), `rank_spontaneous` (rayon, exclusion des entreprises avec une offre du domaine pour le **contrat visé**, au niveau SIREN si dispo, `volume_suspect` écarté, score √(c_intensite × c_embauche) — D13). Décision **D19**.
- App : adresse + rayon dans la barre latérale (clés `adresse`, `rayon` dans `PROFILE_KEYS`/`PROFILE_LABELS`, consigne CLAUDE.md respectée), marqueur + cercle du rayon, couche 🟠 (300 premières), popup (secteur, effectif, score, signal, lien Annuaire des entreprises), onglets « Offres » / « Candidatures spontanées » triées, métrique, légende ; la couche bleue suit le rayon ; `search_history(top=…)` reçoit les SIRET des premières entreprises orange.
- Correctif : l'app plantait sans offres Adzuna (`region_requete` absente pour LBA) → région déduite du code postal ; pied de page avec les sources réellement chargées.
- `tests/test_spontaneous.py` (10 tests, sans réseau) ; 157 tests OK ; parcours vérifié avec AppTest.
- Synchronisation avec `main` : mes 3 commits T40 n'étaient pas poussés → rebase sur le travail d'Emma, Mathis et Celia ; conflits `TACHES.md` / `DECISIONS.md` résolus en gardant les deux versions. Ma décision **renumérotée D16 → D19** (D16, D17 et D18 pris entre-temps par Celia, Emma et Mathis). Après rebase : **174 tests OK**, ruff OK.

**Résultats / chiffres clés :**
- Rennes, données factices : 236 entreprises orange à 20 km (Tous), 250 en stage. Offres LBA réelles (sans filtre data) : 46 à 10 km, 108 à 50 km.

**Problèmes / points d'attention pour l'équipe :**
- Sur mon pod, `entreprises.parquet` / `scores.parquet` sont **factices** (générés pour développer) : il faut les vrais de Mathis (`build_all.py --share`) pour la démo.
- `uv run ruff format .` reformate aussi les blocs Python des `.md` (journal d'Emma touché puis remis en état) : formater ses propres fichiers.

**Prochaine étape :**
- T51 (recruteurs LBA dans la couche orange), T41 / T42 (filtres, poids).

---

## 2026-11-27 — T17 : données LBA partagées sur S3 (Onyxia)

**Fait :**
- `.env` créé sur le pod Onyxia (clé LBA production) ; `uv sync`.
- `uv run python scripts/collect_lba.py` : export du 2026-11-27 (775,8 Mo) → **12 748 offres** (87 % avec SIRET, 768 déléguées à une école) + **382 180 recruteurs potentiels**, chiffres identiques à la collecte locale.
- `python3 scripts/share_s3.py data/raw/offres_raw/lba.parquet data/raw/lba_recruteurs.parquet` → fichiers dans l'espace S3 privé (6,2 Mo + 43,3 Mo), liens valables 24 h.

**Problèmes / points d'attention pour l'équipe :**
- `uv run python scripts/share_s3.py` échoue (`botocore` absent du venv) : utiliser le `python3` système d'Onyxia, comme indiqué dans CLAUDE.md.
- Les liens expirent au bout de 24 h : relancer `share_s3.py` pour en régénérer.

**Prochaine étape :**
- Brancher les recruteurs LBA dans le score (opportunité cachée) et sur la carte.

---

## 2026-11-27 15:00 — Fin de session locale (Windows) → bascule sur Onyxia

**Fait :**
- Collecte T11 relancée avec la clé **production** : à jour (export LBA du 2026-11-27 3 h ; le prochain sort demain vers 3 h).
- `.env` local nettoyé : clé production dans `LBA_API_TOKEN` (le code ne lit que ce nom), ancienne clé gardée sous `LBA_API_TOKEN_SANDBOX`.
- Poste local : `uv` installé via pip (`python -m uv …`, la commande `uv` seule n'est pas dans le PATH) ; identité Git réglée pour ce dépôt.

**Non fait — partage S3 des fichiers LBA :**
- `scripts/share_s3.py` exige les identifiants S3 SSP Cloud, absents sur le poste local → **rien n'a été déposé sur S3**.
- Les fichiers `data/raw/offres_raw/lba.parquet` et `data/raw/lba_recruteurs.parquet` n'existent que sur le PC local.

**Prochaine étape (sur Onyxia) :**
1. `git pull --rebase`, `uv sync`, `cp .env.example .env` puis renseigner `LBA_API_TOKEN` (clé **production**).
2. `uv run python scripts/collect_lba.py` → 1 seul appel API, ~2 min (export de 776 Mo) ; plus simple que de transférer les fichiers depuis le PC.
3. `uv run python scripts/share_s3.py data/raw/offres_raw/lba.parquet data/raw/lba_recruteurs.parquet` (identifiants S3 déjà présents sur Onyxia) → envoyer les commandes `curl` à l'équipe **en message privé**.
4. Prochaine tâche à choisir : brancher les recruteurs LBA dans le score (opportunité cachée) et sur la carte.

---

## 2026-11-27 — Tâche T11 : collecteur La bonne alternance

**Fait :**
- Collecteur `radar/collect/lba.py` + script `scripts/collect_lba.py` : un seul appel à `/job/v1/export` récupère **toute la France** (offres + recruteurs) ; repli `--search` par département / codes ROME.
- Export conservé dans `data/raw/lba/` et retéléchargé seulement s'il a changé (`--force` pour forcer) ; `--fichier` pour retraiter sans réseau.
- Nouveau schéma `recruteurs_lba` (dans `radar/schemas.py` et `ARCHITECTURE.md`) ; tests sans réseau (`tests/test_lba.py`).

**Fichiers touchés :**
- `radar/collect/lba.py`, `scripts/collect_lba.py`, `tests/test_lba.py`, `radar/schemas.py`, `docs/ARCHITECTURE.md`, `docs/SOURCES.md`

**Résultats / chiffres clés :**
- **12 748 offres** d'alternance actives (87 % avec SIRET), mais **~30 seulement en data**.
- **382 180 recruteurs potentiels** (SIRET, NAF, taille, lat/lon, codes ROME), dont **28 845 avec un ROME data** (537 en Ille-et-Vilaine) → c'est le vrai apport de LBA pour l'opportunité cachée.

**Problèmes / points d'attention pour l'équipe :**
- ⚠️ Clé **sandbox** = données de recette factices (~970 offres). Il faut une clé **production** dans `LBA_API_TOKEN` ; le collecteur affiche une alerte sinon.
- Offres `delegue_ecole = True` (768) : le SIRET est celui de **l'école**, à exclure du score.
- Recruteurs dans l'export : reconnus par `partner_label == "recruteurs_lba"` (ils ont un bloc `offer` factice).
- Tailles LBA en tranches texte (`10-19`…) ≠ codes INSEE ; NAF au format `46.34Z`.

**Prochaine étape :**
- Brancher les recruteurs dans le score (composante opportunité cachée) et dans la carte.
