# Journal — Maxence

> Une entrée par session ou par tâche terminée, **la plus récente en haut**. Seul son propriétaire écrit dedans.

---

## 2026-11-27 — T75 : plantage avec les données factices (mon code de T26)

**Fait :**
- Bug trouvé par Celia : `get_families` lisait les colonnes `n_*_domaine_siren`, absentes des scores factices → Explorer plantait.
- Correction : lecture des seules colonnes présentes (`app/commun.py`) ; `radar/familles.py` accepte les deux formats (vrais scores au niveau SIREN, ou comptes par site additionnés, SIREN retrouvé par le SIRET).
- Test ajouté (`tests/test_familles.py`) ; AppTest avec des données factices générées à part : Rennes → 214 candidatures spontanées, sans erreur.
- Au passage : l'utilisateur ne voyait plus de candidatures spontanées ; sur les vraies données, l'app en affiche bien 4 346 à Rennes → probablement la ville oubliée après le redémarrage de l'app.

---

## 2026-11-27 — T26 (suite) : case « Masquer » retirée

**Fait :**
- Discussion : les cases « Une ligne par entreprise » et « Masquer… » ne cachent aucune **offre** (couche bleue), seulement des entreprises de la couche orange. Mais le nombre d'offres du groupe compte toute la France : masquer pouvait faire perdre une société proche sans montrer d'offre du groupe à côté.
- Décision : **tout reste affiché sur la carte**. Case « Masquer les sociétés dont le groupe publie déjà des offres » retirée (`app/vues/explorer.py`, `app/commun.py` : `WIDGET_KEYS`, profil, libellés). La mention « Groupe … : N offres » reste.
- « Une ligne par entreprise » (T57, Celia) : inchangée.
- D36, L7 et T26 mises à jour. 348 tests OK, ruff OK ; AppTest Toulouse : plus de case, 22 lignes signalées.

---

## 2026-11-27 — T26 : familles de marque

**Fait :**
- Explication et choix ensemble : la tâche proposait d'**exclure** les sociétés d'un groupe qui publie déjà ; on a choisi de les **garder en les signalant** (B), avec une case « Masquer » **décochée par défaut**.
- `radar/familles.py` : clé de marque (premier mot du nom normalisé, deux mots si le premier est générique), familles d'ETI/GE d'au moins 2 sociétés ; offres des sœurs comptées selon le contrat visé ; phrase « Groupe Thales : 3 offres déjà publiées ». Liste de mots génériques revue sur les plus grosses familles (société, caisse, institut, ministère, casino…).
- App : colonne « Groupe » dans la liste, ligne 🏢 dans la fiche de la carte et dans la fiche, case « Masquer les sociétés dont le groupe publie déjà des offres » (clé de profil `masquer_groupe`), familles calculées au chargement (≈ 3 s, en cache).
- Décision **D36**, L7 mise à jour.

**Fichiers touchés :**
- `radar/familles.py` (nouveau), `tests/test_familles.py` (nouveau, 4 tests), `app/commun.py`, `app/vues/explorer.py`, `app/fiche_ui.py` (Celia), `app/carte.py` (Mathis), `docs/DECISIONS.md`, `docs/LIMITES.md`, `docs/ARCHITECTURE.md`, `docs/TACHES.md`

**Résultats / chiffres clés :**
- 5 583 familles ; 200 publient des offres data ; 1 214 sociétés sœurs signalées.
- Toulouse 20 km : 22 des 500 premières entreprises signalées (Airbus · 27 offres, Axa · 21, Talan · 10, Pierre Fabre · 4…) ; case cochée → elles disparaissent.
- 348 tests OK, ruff OK.

**Points d'attention :**
- Regroupement par le nom : approximatif (Société Générale non reliée, homonymes possibles entre grandes sociétés). Compléter `GENERIC_WORDS` si un faux groupe apparaît.

---

## 2026-11-27 — T66 : filtre « Régions » supprimé

**Fait :**
- Discussion : la tâche proposait de masquer le filtre quand une ville est choisie ; comme la ville est déjà demandée, on a décidé de le **supprimer complètement**.
- Retiré de la fenêtre « Filtres » (`app/vues/explorer.py`), de `WIDGET_KEYS`, `profile_keys()` (sans argument maintenant), `PROFILE_LABELS` et `filter_offers` (`app/commun.py`), et de `app/vues/mon_espace.py` ; exemples mis à jour dans `app/compte.py` et `docs/GUIDE.md`.
- Décision **D35**.
- Note de Celia lue : elle a corrigé un plantage de mon code de T65 sur les grandes villes (limite de pandas pour la mise en couleur, T71) ; la liste affiche désormais les 500 premières lignes.

**Résultats :** AppTest : plus de champ « Régions » (filtres restants : niveau d'études, taille, secteur) ; Explorer avec Rennes et Mon espace s'affichent sans erreur. 344 tests OK, ruff OK.

**Points d'attention :** un profil enregistré avec des régions les perd sans erreur ; d'anciennes recherches de l'historique peuvent encore afficher « regions : … » dans leur résumé.

---

## 2026-11-27 — T65 (suite) : dégradé d'orange selon le score

**Fait :**
- À ma demande, plus de nuances : `score_color` dans `radar/paliers.py`, dégradé continu d'orange très clair (score 0) à orange foncé (score 1), texte noir ou blanc selon le fond.
- Liste : fond de la colonne « Score » dans ce dégradé (score brut).
- Carte : remplissage des points dans le dégradé, **étalé entre le plus faible et le plus fort score affichés** (à Rennes 20 km, les 300 points montrés vont de 0,80 à 0,99 : sans ça, tous de la même couleur). Taille des points toujours selon le palier.
- D32 complétée.

**Fichiers touchés :**
- `radar/paliers.py`, `tests/test_paliers.py` (+1 test), `app/carte.py`, `app/vues/explorer.py`, `docs/DECISIONS.md`, `docs/TACHES.md`

**Résultats :** 316 tests OK, ruff OK ; app vérifiée (accueil, Rennes).

---

## 2026-11-27 — T65 : score en mots et en couleurs

**Fait :**
- Discussion des options (seuils fixes, quantiles de la recherche, mixte) sur les vraies distributions du score ; choix **mixte** : un palier = être parmi les meilleures de la recherche **et** au-dessus d'un score minimal.
- `radar/paliers.py` : 4 paliers ●●● Cible prioritaire (10 %, ≥ 0,60) / ●●○ Bonne cible (30 %, ≥ 0,45) / ●○○ À considérer (60 %, ≥ 0,30) / ○○○ Moins indiquée ; couleurs de l'orange foncé au gris ; ex æquo traités prudemment.
- App : colonne « Priorité » colorée dans la liste (règle en info-bulle, score à côté), points de la carte colorés et dimensionnés par palier (score dans l'info-bulle et la fiche de la carte), « Priorité » dans la fiche avec le score en dessous.
- Libellés de priorité plutôt que « probable » (le score n'est pas une probabilité ; la chance de réponse simulée est affichée à part).
- Décision **D32**.

**Fichiers touchés :**
- `radar/paliers.py` (nouveau), `tests/test_paliers.py` (nouveau, 6 tests), `app/vues/explorer.py` et `app/fiche_ui.py` (Celia), `app/carte.py` (Mathis), `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/TACHES.md`

**Résultats / chiffres clés :**
- Rennes 20 km (stage) : 435 cibles prioritaires, 869 bonnes, 1 304 à considérer, 1 738 moins indiquées ; en tête Hellowork, Ouest-France, Treezor, Beetween. Guéret alternance : 20 / 37 / 60 / 146 (le minimum joue).
- 311 tests OK, ruff OK.

**Problèmes / points d'attention pour l'équipe :**
- **@celia** (T64) et **@mathis** : j'ai touché la liste (`explorer.py`), la fiche (`fiche_ui.py`) et les points de la carte (`carte.py`), quelques lignes chacun ; toute la logique est dans `radar/paliers.py`.
- **@mathis** (T69) : si le score v1 change de distribution, revoir les minima dans `TIERS`.

---

## 2026-11-27 — T55 (suite) : effacer la ville, codes postaux regroupés

**Fait :**
- **On ne pouvait pas effacer la ville** pour en choisir une autre : Streamlit n'affiche la croix d'effacement que si la liste est créée avec `index=None` (vérifié dans le code du composant). Ajouté dans `app/vues/explorer.py` (fichier de Celia, une ligne + le texte d'aide).
- **Une ligne par ville** avec tous ses codes postaux entre parenthèses : « Rennes (35000, 35200, 35700) », « Paris (75001, …, 75020, 75116) ». On peut aussi taper un code postal pour trouver sa ville. 34 964 choix au lieu de 35 493.
- D28 et T55 mises à jour.

**Fichiers touchés :**
- `radar/communes.py` (colonne `codes_postaux` au lieu de `code_postal`), `tests/test_communes.py`, `app/vues/explorer.py`, `app/commun.py` (docstring), `docs/DECISIONS.md`, `docs/TACHES.md`

**Résultats / chiffres clés :**
- AppTest : Rennes → liste des entreprises affichée ; effacer → retour à vide sans erreur ; Nantes (44000, 44100, 44200, 44300) → liste affichée. Tous les tests OK, ruff OK.

**Problèmes / points d'attention pour l'équipe :**
- **@celia** : j'ai touché `app/vues/explorer.py` (le `selectbox` de la ville seulement : `index=None` + placeholder).
- Les villes enregistrées dans un profil ou un historique avec l'ancien libellé (« Rennes (35000) ») ne sont plus reconnues : il faut les rechoisir une fois.

---

## 2026-11-27 — T55 : suggesteur de ville

**Fait :**
- Tâche ajoutée à ma demande (T55) : on tape le nom de la ville et on la **valide dans une liste déroulante « Ville (code postal) »**, au lieu d'une adresse libre.
- `radar/communes.py` : toutes les communes de France via geo.api.gouv.fr (un seul appel, cache disque 30 jours), une ligne par (commune, code postal), triées par population ; homonymes partageant un code postal rendus uniques ; repli hors ligne sur les communes du référentiel.
- App : `st.selectbox` « Ta ville » (on tape pour filtrer), clé de profil `ville` (remplace `adresse`), point de départ = centre de la commune ; textes « saisis ton adresse » remplacés.
- Décision **D28**.

**Fichiers touchés :**
- `radar/communes.py` (nouveau), `tests/test_communes.py` (nouveau, 3 tests), `app/streamlit_app.py`, `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/TACHES.md`

**Résultats / chiffres clés :**
- 35 493 choix (34 969 communes). AppTest : premier affichage 13 s (téléchargement de la liste, ensuite en cache), Rennes (35000) → 64 offres, 4 346 entreprises 🟠 ; Lyon (69003) → 459 offres, 12 972 entreprises.
- 269 tests OK, ruff OK.

**Problèmes / points d'attention pour l'équipe :**
- Les profils enregistrés avec une `adresse` doivent rechoisir leur ville une fois.
- Paris, Lyon, Marseille : tous les codes postaux pointent sur le même centre (amélioration possible : arrondissements municipaux).

**Prochaine étape :**
- Choisir la tâche suivante (T26 familles de marque, T34 validation…).

---

## 2026-11-27 — T51 : recruteurs LBA dans la couche orange

**Fait :**
- `radar/recruteurs.py` : une entreprise du rayon est marquée `recruteur_lba` si La bonne alternance la signale comme recruteur potentiel d'alternants sur un code ROME **non ambigu** du domaine (lecture DuckDB des seuls SIRET affichés).
- Nouvelle composante du score pondéré **« Recruteur d'alternants (LBA) »** (`c_recruteur_lba`, curseur, poids 2 par défaut), qui ne compte qu'en **alternance** et « Tous ». Dans les autres cas son poids est ignoré (et l'opportunité cachée est ignorée en « Tous », où elle valait toujours 0).
- Une composante sans poids n'apparaît plus dans la liste ni dans la fiche (apport vide au lieu de +0,00).
- Dans `app/streamlit_app.py`, une seule ligne changée (`get_nearby`) pour ne pas gêner T32 (Mathis, fiche de la carte et liste) ni T43 (Celia, panneau du bas) : le curseur, la colonne et la ligne de la fiche viennent tout seuls de `COMPONENTS`.
- Décision **D26**.

**Fichiers touchés :**
- `radar/recruteurs.py` (nouveau), `tests/test_recruteurs.py` (nouveau, 6 tests), `radar/spontaneous.py`, `tests/test_weights.py`, `app/streamlit_app.py`, `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/TACHES.md`

**Résultats / chiffres clés :**
- France : 28 733 recruteurs LBA sur un ROME data ; 12 378 dans le référentiel, dont 11 171 sans offre data (couche orange).
- Rennes, 20 km, alternance : 206 entreprises marquées sur 4 447 ; en tête Infotel Conseil, Riot Security, Open, Celad, Coexya. En stage : critère ignoré, classement inchangé.
- 255 tests OK, ruff OK.

**Problèmes / points d'attention pour l'équipe :**
- **@emma (T28)** : `radar/recruteurs.py` (`lba_recruiter_sirets`, `domain_rome_codes`) est réutilisable pour `c_embauche`.
- Il faut `data/raw/lba_recruteurs.parquet` (T17) ; sans lui, la composante vaut 0 et rien ne casse.

**Prochaine étape :**
- À choisir avec l'équipe (pitch : T60 / T61 scénario de démo ?).

---

## 2026-11-27 — T37 : P(réponse) dans l'app

**Fait :**
- `radar/response/predict.py` : lit `p_reponse.parquet` pour les seuls SIRET affichés (DuckDB) et ajoute l'effet de la distance au logit avec le coefficient de `modele_reponse.json` (D18). Stage / alternance → la ligne du contrat ; « Tous » → moyenne des deux ; « Emploi » → pas de P(réponse).
- App : réglage **« Classer les entreprises 🟠 par : Score / P(réponse) simulée »** (clé `tri`, enregistré au profil), colonne « P(réponse) simulée » en % dans la liste, ligne dans la fiche de la carte, **bandeau « 🧪 Démonstrateur — réponses simulées »** dès qu'une probabilité est affichée. Si le modèle manque, si le domaine n'est pas couvert ou en emploi : message qui explique pourquoi, classement par score.
- Décision **D23** ; L15 mise à jour ; nouvelle tâche **T53**.

**Fichiers touchés :**
- `radar/response/predict.py` (nouveau), `tests/test_predict.py` (nouveau, 5 tests), `app/streamlit_app.py`, `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/LIMITES.md`, `docs/TACHES.md`

**Résultats / chiffres clés :**
- 221 tests OK, ruff OK. AppTest (Rennes, 20 km) avec un `p_reponse` construit à partir des coefficients de `docs/MODELE_REPONSE.md` : bandeau affiché, tri par P(réponse) qui reclasse la liste, message en « Emploi », probabilités plus hautes en alternance (coefficient +0,33).

**Problèmes / points d'attention pour l'équipe :**
- Sur mon pod, j'ai reconstruit les **vraies** entreprises SIRENE et les scores (`build_all.py --sirene`) : il n'y a plus de données factices. Mais je n'ai que les offres **LBA** (pas Adzuna) → `c_intensite` vaut 0,5 partout et `scripts/build_response.py` plante (« Singular matrix ») → T53.
- **@mathis** : il me faut tes `scores.parquet`, `entreprises.parquet`, `p_reponse.parquet` et `modele_reponse.json` (via `build_all.py --share` / `share_s3.py`, en MP) pour voir T37 avec les vraies probabilités.
- ✅ **Réglé** : fichiers de Mathis reçus (406 266 établissements, 402 483 P(réponse) par contrat, offres Adzuna). Vérifié avec AppTest, Rennes 20 km, stage : 4 392 entreprises 🟠, bandeau affiché ; tri par score → Spikeelabs, Kanoma, Infotel Conseil (P ≈ 30–35 %) ; tri par P(réponse) → Davricourt (38 %), Avanci, Esri France.

**Prochaine étape :**
- Récupérer les fichiers de Mathis et vérifier l'app de bout en bout ; T51.

---

## 2026-11-27 — T42 : curseurs de poids du score orange

**Fait :**
- Score de la couche 🟠 = **moyenne pondérée** de 5 composantes (0 à 1) : intensité dans le domaine et besoin attendu (D13), **proximité** (1 à l'adresse, 0 au bord du rayon), **opportunité cachée** (offres du domaine mais aucune pour le contrat visé), dynamisme (neutre tant que T22 manque).
- Bloc « ⚖️ Poids du score 🟠 » dans la barre latérale : 5 curseurs de 0 à 5 (défaut 3 / 3 / 1 / 1 / 0) avec explication au survol, bouton « Poids par défaut ». Le classement, la carte et la liste se recalculent à chaque changement.
- **Explicabilité** : colonnes « + Intensité », « + Proximité »… dans la liste (leur somme = le score) et barres de décomposition dans la fiche de chaque point de la carte.
- Tous les poids à 0 → repli sur le score D13. Poids enregistrés dans le profil (clés `poids_*` dans `PROFILE_KEYS` / `PROFILE_LABELS`).
- Décision **D22**.

**Fichiers touchés :**
- `radar/spontaneous.py` (`COMPONENTS`, `DEFAULT_WEIGHTS`, `add_user_components`, `weighted_score`, paramètre `weights` de `rank_spontaneous`), `app/streamlit_app.py`, `tests/test_weights.py` (nouveau, 6 tests), `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/TACHES.md`

**Résultats / chiffres clés :**
- 216 tests OK, ruff OK. AppTest (Rennes, 20 km, données factices) : poids par défaut → Sigmaouest (0,81) en tête ; proximité seule → entreprise à 70 m en tête (score 1,00) ; stage + opportunité cachée à 5 → les entreprises qui recrutent en emploi data sans stage passent devant ; le bouton remet bien 3/3/1/1/0.

**Problèmes / points d'attention pour l'équipe :**
- Le curseur « Dynamisme » ne change rien tant que T22 (finances) n'est pas faite : composante à 0,5 partout (L10).
- `rank_spontaneous(...)` sans `weights` garde l'ancien score D13 : rien ne casse pour qui l'appelle ailleurs.

**Prochaine étape :**
- T51 (recruteurs LBA dans la couche orange) ; donner mon avis sur la proposition D21 d'Emma.

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
