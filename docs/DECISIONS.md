# Décisions

> Une entrée par choix structurant (stack, modèle, format de données, découpage du travail…). Les plus récentes en haut. Permet à chaque session Claude de comprendre **pourquoi** les choses sont comme elles sont.

## Modèle

```markdown
### D<num> — Titre court (AAAA-MM-JJ, @prenom)
**Contexte :** quel problème / quelle question.
**Décision :** ce qu'on a choisi.
**Alternatives écartées :** et pourquoi.
**Conséquences :** ce que ça implique pour les autres.
```

---

### D11 — Référentiel SIRENE : fusion des deux versions de T20 (2026-11-27, @celia)
**Contexte :** T20 a été réalisée deux fois en parallèle (@celia, puis @mathis, car le push de Celia était bloqué). Les deux versions lisaient les mêmes stocks SIRENE à distance avec DuckDB, avec le même filtre (actif, ≥ 10 salariés, `'NN'` exclu, NAF rév. 2) et donnaient 406 266 établissements.
**Décision :** la base est la version de Mathis : T21 utilise déjà `effectif_estime` et le `nom` de l'unité légale, et `scripts/extract_sirene.py` appelle `extract()` / `save()`. Ajouts repris de la version de Celia : prénom + nom pour les entrepreneurs individuels sans dénomination, colonnes `tranche_libelle` et `adresse` (vide si diffusion partielle, comme lat/lon), option `--dep` pour tester sur un département, tests sur les tranches et la requête.
**Alternatives écartées :** garder les deux modules (doublon) ; la table NAF en CSV versionné de Celia (le parquet NAF de data.gouv donne aussi section et division) ; `procedure_collective = False` par défaut (NA est plus juste tant que T23 n'est pas faite).
**Conséquences :** un seul point d'entrée, `uv run python scripts/extract_sirene.py [--dep 35]`. `radar/naf_rev2.csv` et son exception dans `.gitignore` sont supprimés.

### D10 — offres.parquet : T13 classe, T21 rapproche (2026-11-27, @emma)
**Contexte :** `offres.parquet` reçoit des colonnes de deux tâches menées en parallèle : `domaine`/`contrat` (T13, @emma) et `siret_match`/`match_score`/`match_methode` (T21, @mathis). Il ne faut pas que l'une écrase le travail de l'autre.
**Décision :** T13 (`radar/process/classify.py`) écrit `offres.parquet` à partir de toutes les offres brutes. Il remplit le SIRET seulement quand la source le donne (`siret_source`), retire celui des offres déléguées à une école (`siret_ecole_exclu`) et marque les autres `a_rapprocher`. T21 relit `offres.parquet` et ne complète que les lignes `a_rapprocher`, avec sa propre valeur de `match_methode`. Chaque classement garde la règle qui l'a décidé (`domaine_regle`, `contrat_regle`) pour pouvoir l'expliquer. Pour le contrat, le titre l'emporte sur le `contract_type` d'Adzuna (rarement rempli, et seulement permanent/contract).
**Alternatives écartées :** que T21 écrive son propre fichier (deux versions des offres à réconcilier dans T50) ; que T13 attende T21 (on perdrait du temps sur le chemin de la V1).
**Conséquences :** ordre du pipeline (T50) : collecteurs → `classify_offres.py` → rapprochement T21 → score. `quick_filter.py` (T39) peut être remplacé par `offres.parquet` dans l'app (à voir avec Maxence).

### D9 — Dictionnaire des domaines : codes ROME sûrs, codes ambigus et mots-clés (2026-11-27, @emma)
**Contexte :** classer chaque offre par domaine (T6 → T13). La bonne alternance fournit des codes ROME, mais pas Adzuna (titre seulement). Certains codes ROME sont ambigus (« Chargé d'études commerciales » peut être un poste data ou marketing).
**Décision :** `radar/domains.yaml` décrit 5 domaines, dans l'ordre data, informatique, finance, marketing, rh (l'ordre départage les cas ambigus : data gagne). Pour chacun :
- `rome` : les codes sûrs, chacun dans un seul domaine ;
- `rome_partiel` : les codes ambigus, qui ne comptent que si le titre contient un mot-clé du domaine ;
- `mots_cles` et `exclusions` : des expressions régulières sur le titre.

Règle (`radar/domains.py › classify`) : code ambigu confirmé par le titre, sinon code sûr, sinon titre seul, sinon `autre`. Les codes ont été vérifiés avec l'API ROME 4.0 (1 923 métiers) et leurs libellés recopiés. Les mots-clés data reprennent ceux de `quick_filter.py` (T39) : les verdicts sont identiques sur ses titres de test.
**Alternatives écartées :** des mots-clés seuls (on perdrait le ROME, fiable quand il existe) ; des codes seuls (inutilisables pour Adzuna).
**Conséquences :** T13 s'appuie sur `classify` et peut y ajouter la description. Ajouter un domaine = ajouter un bloc dans le YAML, sans toucher au code (mais `fake_data.DOMAINS` doit suivre : un test le vérifie). Les titres en anglais hors data sont mal couverts (« Accounting Generalist » → `autre`).

### D8 — Carte à deux couches : offres réelles / candidature spontanée (2026-11-27, @mathis)
**Contexte :** l'équipe veut que la démo repose sur une carte montrant à la fois les vraies offres et les entreprises susceptibles d'accepter une candidature spontanée.
**Décision :** une carte folium, deux couches activables. 🔵 Offres réelles (filtrées domaine × contrat visé, lien vers l'annonce). 🟠 Candidature spontanée : entreprises **sans offre correspondante**, classées par score ou P(réponse). Les deux couches sont exclusives (une entreprise avec une offre correspondante est en bleu).
**Conséquences :** l'appli a besoin de `offres.parquet` (avec SIRET quand il est connu, pour l'exclusion) et de `scores.parquet` / `p_reponse.parquet`. La couche 1 peut être faite dès maintenant (T39).

### D7 — Contrat de données vérifiable en code + données factices (2026-11-27, @emma)
**Contexte :** T5 doit produire des données qui respectent les schémas de `ARCHITECTURE.md`, et chaque module doit pouvoir vérifier qu'il les respecte aussi.
**Décision :** `radar/schemas.py` recopie en code les colonnes minimales du tableau de `ARCHITECTURE.md`, avec `check_columns(df, nom)` (les colonnes en plus sont permises). Les offres brutes vont dans `data/raw/offres_raw/<source>.parquet`, comme le prévoit T12. Le générateur factice (`radar/fake_data.py`) est reproductible (graine fixe) et ne décrit que des entreprises inventées : SIRET aléatoires mais valides (clé de Luhn), URL en `example.org`, descriptions marquées `[DONNÉE FACTICE]`.
**Alternatives écartées :** un générateur sans vérification de schéma (les écarts n'apparaîtraient qu'au branchement des vraies données, à H+8).
**Conséquences :** si on change un schéma, il faut mettre à jour **le tableau et `schemas.py`**. Les fichiers `scores`, `candidatures_simulees` et `p_reponse` factices ont les bonnes colonnes, mais leurs formules sont provisoires : T30/T31 et T35/T36 les remplaceront.

### D6 — Modèle de réponse entraîné sur des réponses simulées (2026-11-27, @mathis)
**Contexte :** l'équipe veut un modèle « qui va répondre à une candidature spontanée », mais aucune donnée ouverte ne contient ces réponses. Le but pour le hackathon : montrer que la chaîne fonctionne.
**Décision :** les entreprises et leurs variables sont réelles ; seule la réponse est simulée, selon une règle paramétrique (paramètres documentés dans `radar/response/params.yaml`). On entraîne un modèle et on montre la calibration, l'AUC et les paramètres retrouvés.
**Alternatives écartées :** générer les réponses avec un LLM (non reproductible, payant, règle inconnue donc on ne peut pas vérifier que le modèle la retrouve).
**Conséquences :** **toujours étiqueter comme simulé** (app + slides). Réponse préparée pour le jury : la chaîne sera réentraînée sur de vrais retours d'utilisateurs.

### D5 — Pas de collecte quotidienne (2026-11-27, @mathis)
**Contexte :** hackathon de 24 h.
**Décision :** une seule collecte (instantané). Pas d'historique, pas de planification.
**Conséquences :** le score décrit le marché à l'instant T ; à présenter comme une perspective (« avec un historique, on mesurerait la dynamique »).

### D4 — Domaine paramétrable ; stage, alternance et emploi (2026-11-27, @mathis)
**Contexte :** l'appli doit servir à tous les étudiants. Les offres d'emploi d'un domaine sont un signal de besoin, même si l'étudiant cherche un stage.
**Décision :** chaque offre est classée par `domaine` (dictionnaire ROME + mots-clés dans `radar/domains.yaml`) et par `contrat` (stage / alternance / emploi). L'intensité se calcule tous contrats confondus ; l'opportunité cachée = besoin dans le domaine, mais aucune offre du contrat visé. Data est le domaine de la démo.
**Conséquences :** `scores.parquet` a une ligne par (siret, domaine).

### D3 — Échelle France entière, sans données propres à l'ENSAI (2026-11-27, @mathis)
**Contexte :** l'équipe veut une appli nationale, pas limitée à l'ENSAI.
**Décision :** référentiel SIRENE France ; offres via La bonne alternance (nationale, avec SIRET) et Adzuna (par département, dans la limite du quota). Pas d'export de stages d'école : validation par stabilité, sensibilité et cohérence externe.
**Alternatives écartées :** cache Bretagne seul (trop limité pour le pitch).
**Conséquences :** il faut DuckDB et du parquet pour tenir le volume ; on garde un cache de démo figé pour la robustesse.

### D2 — Ne pas dépendre de l'API Offres d'emploi France Travail (2026-11-27, @mathis)
**Contexte :** l'API n'est plus exposée sur francetravail.io (accès suspendu, à demander via un formulaire).
**Décision :** le signal « offres » repose sur Adzuna (dont `top_companies`), l'API La bonne alternance (avec SIRET) et les ATS publics. On demande quand même l'accès à France Travail ; s'il arrive, c'est un bonus.
**Conséquences :** quota Adzuna serré → collecte ciblée sur la Bretagne avec cache ; volume d'offres à valider dès qu'on a la clé.

### D1 — Coordination via fichiers Markdown dans le dépôt (2026-11-27, @mathis)
**Contexte :** plusieurs personnes, chacune avec sa propre session Claude Code, sur le même dépôt.
**Décision :** `CLAUDE.md` comme règles communes ; `docs/TACHES.md` pour se répartir le travail ; un journal par personne dans `docs/journal/` pour éviter les conflits Git.
**Alternatives écartées :** un seul fichier d'avancement partagé (conflits de merge permanents).
**Conséquences :** chaque session suit le rituel décrit dans `CLAUDE.md`.
