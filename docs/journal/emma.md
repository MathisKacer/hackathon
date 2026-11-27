# Journal — Emma

> Une entrée par session ou par tâche terminée, **la plus récente en haut**. Seule Emma écrit dans ce fichier.

---

## 2026-11-27 — T8 : titres anglais mal classés ✅

**Fait :**
- Récupération des **vraies offres Adzuna** de Mathis (lien S3 privé, `curl`) : 10 776 offres dans `data/raw/offres_raw/adzuna.parquet` sur mon pod. `lba.parquet` est encore factice chez moi, donc seules les offres Adzuna ont été analysées.
- Mesure de la situation de départ, puis ajout de mots-clés anglais (et de quelques oublis) dans `radar/domains.yaml`, marqués `# T8`. J'ai vérifié **chaque bascule** de domaine sur les vraies offres, pas seulement les sorties de « autre ».
- Correction d'un bug : « Talent Acquisition » était classé marketing (mot-clé `acquisition` trop large).
- 27 tests de plus dans `tests/test_domains.py` (titres réels relevés, et pièges qui doivent rester « autre »).
- Docs : D17 dans `DECISIONS.md`, T8 en « Fait ».

**Fichiers touchés :**
- `radar/domains.yaml`, `tests/test_domains.py`
- `docs/DECISIONS.md`, `docs/TACHES.md`, `docs/journal/emma.md`

**Résultats / chiffres clés (10 776 offres Adzuna réelles, toutes issues de la recherche « data ») :**

| Domaine | Avant | Après |
|---|---|---|
| autre | 4 488 (41,6 %) | 3 939 (36,6 %) |
| data | 3 128 | 3 209 |
| informatique | 1 972 | 2 533 |
| finance | 616 | 549 |
| marketing | 416 | 371 |
| rh | 156 | 175 |

- Titres anglais classés « autre » : 941 → 746. Ceux qui restent sont surtout hors de nos 5 domaines (commerce, recherche clinique, « Project Manager » générique) : c'est voulu.
- Principales bascules : autre → informatique 462 (Business Analyst, architectes de solutions, Product Manager, consultants SAP, SRE…), autre → data 64 (Analytics Engineer, MLOps, Decision Scientist, Pricing Analyst, RWE), autre → finance 22 (Accountant, Capital Markets, Controlling), autre → rh 11 (People Partner, Recruitment), marketing → rh 13 (Talent Acquisition).
- Échantillon de 45 bascules autre → informatique relu à la main : aucune erreur.
- Rappel : 36,6 % de « autre » n'est pas un échec. La recherche Adzuna « data » ramène aussi des offres qui ne citent « data » que dans la description (ex. 142 « Négociateurs immobilier »).
- `pytest` : 190/190 ; ruff OK.

**Problèmes / points d'attention pour l'équipe :**
- **Pour @mathis :** relancer `uv run python scripts/build_all.py` pour que `offres.parquet` et les scores (T30/T31) prennent en compte les nouveaux classements, puis repartager les fichiers.
- Effet de bord assumé : 87 « Business Analyst Crédit/Assurance – Services financiers » passent de finance à informatique (au sens du ROME, ce sont des postes de consultant fonctionnel SI). À revoir si l'équipe préfère les laisser en finance.
- Erreurs connues restantes, rares : « Partnership Manager - Accountant Sector » → finance ; « Finaxys recrute un Project Management Office » → rh (le mot-clé `recrut` attrape le verbe « recrute » : 1 seule offre concernée sur les vraies données, je n'ai pas compliqué la règle pour ça).
- Pas encore vérifié sur les vraies offres La bonne alternance : il faut que Maxence les partage (T17). Elles ont des codes ROME, donc dépendent beaucoup moins des titres.

**Prochaine étape :**
- Selon les besoins de l'équipe : voir les tâches libres dans `TACHES.md`.

---

## 2026-11-27 — T7 : recruteurs La bonne alternance factices ✅

**Fait :**
- `radar/fake_data.py` › `make_recruteurs` : recruteurs potentiels factices au schéma `recruteurs_lba` de Maxence. Ils sont tirés **en dernier**, donc les autres tables restent identiques pour une même graine.
- `scripts/make_fake_data.py` écrit aussi `data/raw/lba_recruteurs.parquet`, au même endroit que le vrai collecteur, et refuse toujours d'écraser sans `--force`.
- 2 tests de plus dans `tests/test_fake_data.py` (schéma, SIRET valides, aucun recruteur avec une offre d'alternance, codes ROME connus, reproductibilité).
- Docs : T7 en « Fait », mention dans `ARCHITECTURE.md`.

**Fichiers touchés :**
- `radar/fake_data.py`, `scripts/make_fake_data.py`, `tests/test_fake_data.py`
- `docs/TACHES.md`, `docs/ARCHITECTURE.md`, `docs/journal/emma.md`

**Choix de réalisme :**
- Un recruteur potentiel est une entreprise **sans offre d'alternance publiée** : on les tire parmi les entreprises factices qui n'en ont pas (les plus grosses plus souvent), et jamais parmi celles en procédure collective.
- ~15 % de petites entreprises (tailles `0-0`, `1-2`, `3-5`, `6-9`) **absentes de `entreprises.parquet`**, comme dans le vrai export : ça permet de tester les jointures qui échouent.
- Tailles au format texte de La bonne alternance (`10-19`…), NAF au format `62.01Z` (comme SIRENE et LBA).
- `code_rome` : 1 à 4 **vrais** codes ROME 4.0 tirés de `domains.yaml` selon le secteur, donc les recruteurs data sont surtout dans l'informatique, le conseil et la finance. Les métiers hors des 5 domaines ne sont pas représentés, ce qui laisse `code_rome` vide pour ~25 % des recruteurs.
- Adresses en « rue Factice », URL en `example.org`, OPCO et IDCC tirés dans des listes réelles.

**Résultats / chiffres clés (graine 42) :**
- 662 recruteurs (85 % dans le référentiel), dont 154 avec un code ROME data et 44 à Rennes.
- Les autres tables sont inchangées (mêmes volumes qu'avant T7).
- `pytest` : 104/104 ; ruff OK.

**Problèmes / points d'attention pour l'équipe :**
- **Pour @maxence (couche orange de la carte) :** `make_fake_data.py --force` donne maintenant des recruteurs pour développer sans les 382 180 vrais. ⚠️ `--force` écrase aussi les fichiers d'offres : à ne pas lancer sur un pod qui a les vraies données.
- Vérification faite pendant T7 : la refonte de T21 par Mathis (`8dc3f96`) complète bien l'`offres.parquet` de T13 selon D10, et les SIRET d'école restent exclus. Rien à corriger.
- Sur mon pod, j'ai relancé `make_fake_data.py --force` : tout y était factice (vérifié avant d'écraser).

**Prochaine étape :**
- T8 (titres anglais) dès que Mathis partage les vraies offres.

---

## 2026-11-27 — T13 : classifieur d'offres ✅

**Fait :**
- `radar/process/classify.py` : `classify_offers(df)` ajoute aux offres brutes `domaine` (via `radar.domains.classify`), `contrat` (stage / alternance / emploi), la règle qui a décidé chacun (`domaine_regle`, `contrat_regle`) et le SIRET quand la source le donne. Les doublons (`source`, `offre_id`) sont supprimés. `summary()` fait un rapport texte.
- `scripts/classify_offres.py` : lit `data/raw/offres_raw/*.parquet`, écrit `data/processed/offres.parquet` et affiche le résumé, dont les titres classés « autre » les plus fréquents, qui serviront pour T8.
- `radar/domains.py` : nouvelle fonction `classify_with_rule` (domaine + règle) ; `classify` reste inchangée.
- `tests/test_classify.py` : 15 tests (règles de contrat, pièges comme « Médecin interne », doublons, SIRET d'école exclu, passage sur les offres factices).
- Docs : D10 dans `DECISIONS.md` (partage de `offres.parquet` entre T13 et T21), colonnes et valeurs de `match_methode` dans `ARCHITECTURE.md`, commande dans `CLAUDE.md`, T13 en « Fait ».

**Fichiers touchés :**
- `radar/process/classify.py`, `scripts/classify_offres.py`, `tests/test_classify.py`, `radar/domains.py`
- `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/TACHES.md`, `docs/journal/emma.md`

**Règles de contrat (la première qui s'applique) :**
1. Le contrat brut dit « Apprentissage » ou « Professionnalisation » (La bonne alternance) → alternance.
2. Le titre contient altern…, apprenti…, contrat pro, work-study → alternance.
3. Le titre contient stage, stagiaire, intern(ship), PFE, trainee → stage.
4. Sinon → emploi.

Le titre l'emporte sur le `contract_type` d'Adzuna (14 offres sur 50 seulement le renseignent, avec « permanent » ou « contract »). « Stage ou alternance » → alternance.

**Résultats / chiffres clés :**
- Sur les offres factices de mon pod (1 701) : tout passe, 100 % d'accord avec le domaine et le contrat factices. Ce n'est **pas** une mesure de qualité, puisque les titres factices sortent de mes propres listes ; ça montre seulement que la chaîne fonctionne. Je n'ai rien écrit dans `data/` (essai en mémoire).
- `pytest` : 94/94 sur tout le dépôt ; ruff OK.

**Problèmes / points d'attention pour l'équipe :**
- **Pour @mathis (T21) :** `offres.parquet` sort de T13 avec `match_methode = "a_rapprocher"` pour les offres Adzuna. T21 peut relire ce fichier et ne compléter que ces lignes (voir D10). Les offres La bonne alternance ont déjà leur SIRET (`siret_source`), sauf celles déléguées à une école (`siret_ecole_exclu`, SIRET retiré, 768 offres selon Maxence).
- **Pour @maxence (app) :** l'app pourra lire `domaine` et `contrat` dans `offres.parquet` au lieu d'utiliser `quick_filter.py`. Je n'ai pas touché à `quick_filter.py` ni à l'app.
- Sur mon pod, `data/raw/offres_raw/` contient encore les offres **factices** : il faut relancer `scripts/classify_offres.py` une fois les vraies offres récupérées (liens S3 de Mathis).
- Pour le domaine, seul le titre est utilisé, pas la description (tronquée à ~500 caractères chez Adzuna, risque de faux positifs). Piste possible plus tard, avec T8.

**Prochaine étape :**
- T7 (recruteurs LBA factices) : débloquée par la fusion de la branche de Maxence.
- T8 (titres anglais) dès que les vraies offres Adzuna sont partagées : `classify_offres.py` affiche déjà les titres « autre » les plus fréquents.

---

## 2026-11-27 — T6 : dictionnaire des domaines ✅

**Fait :**
- `radar/domains.yaml` : 5 domaines (data, informatique, finance, marketing, rh), chacun avec ses codes ROME 4.0 sûrs, ses codes ambigus, ses mots-clés et ses exclusions. La règle de classement est expliquée en tête du fichier.
- `radar/domains.py` : `load_domains()` (domaines dans l'ordre du fichier) et `classify(titre, code_rome)` → domaine ou `autre`. Gère plusieurs codes séparés par des virgules (format de La bonne alternance).
- `tests/test_domains.py` : 35 tests (fichier bien formé, un code ROME dans un seul domaine, mêmes domaines que le générateur factice, titres typiques et pièges).
- Docs : D9 dans `DECISIONS.md`, arborescence dans `ARCHITECTURE.md`, T6 en « Fait », T2 cochée (faite), nouvelle tâche T7 en attente.

**Fichiers touchés :**
- `radar/domains.yaml`, `radar/domains.py`, `tests/test_domains.py`
- `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/TACHES.md`, `docs/journal/emma.md`

**Comment j'ai obtenu les codes ROME :**
- Le fichier open data du ROME (francetravail.org) est **inaccessible depuis Onyxia** : la connexion est coupée.
- J'ai donc utilisé l'API France Travail « ROME 4.0 – Métiers », avec les clés du `.env` : `GET /partenaire/rome-metiers/v1/metiers/metier?champs=code,libelle,domaineProfessionnel(code,libelle,grandDomaine(code,libelle)),appellations(libelle)`, soit 1 923 métiers.
- J'ai choisi les codes à la main, à partir des domaines professionnels (M14 études, M18 SI, M12 comptabilité-gestion, C12/C13 banque-finance, M17/E11/E14 marketing-communication, M15 RH) et d'une recherche de mots-clés dans les appellations. Les libellés du YAML sont recopiés depuis l'API.
- Le script d'extraction n'est pas versionné : c'était un usage ponctuel, et c'est le YAML qui fait foi.

**Résultats / chiffres clés :**
- Nombre de codes sûrs (+ ambigus) : data 18 (+ 8 ambigus), informatique 82, finance 49, marketing 34, rh 11.
- Codes data ajoutés à la liste de `SOURCES.md` : M1422 (directeur d'études socio-éco), M1873 (IA embarquée), K2134 (démographe), H1215 (bio-informaticien). M1824 (BI) est confirmé.
- Codes ambigus data : M1430 (études commerciales), M1435 (tracking), M1201 (analyste financier, quant), M1853 (chef de projet informatique, « projet Data »), M1894 (gestionnaire de bases de données), M1895 (géomaticien), M1888 (modélisation climatique), G1211 (analyste de la performance sportive).
- Les mots-clés data reprennent ceux de `quick_filter.py` (Mathis, T39), avec le même verdict sur ses 18 titres de test. J'ai ajouté des exclusions : datacenter, DPO / protection des données, saisie de données.
- `pytest` : 69/69 sur tout le dépôt ; ruff OK.

**Problèmes / points d'attention pour l'équipe :**
- **Pas encore validé sur de vraies offres** : les données Adzuna de Mathis sont sur son pod, et je n'ai pas relancé de collecte pour ne pas consommer le quota partagé. Pour comparer sur les vraies offres :
  `uv run python -c "import pandas as pd; from radar.domains import classify; df=pd.read_parquet('data/raw/offres_raw/adzuna.parquet'); print(df['titre'].map(classify).value_counts())"`
- Les titres anglais hors data sont mal couverts (« Accounting Generalist » → `autre`) : à compléter dans T13 si besoin.
- Un code sûr l'emporte sur le titre : « Data engineer » avec un code M1805 (développeur) → informatique. C'est voulu, le ROME étant plus fiable que le titre.
- `quick_filter.py` (T39) reste en place : je n'y ai pas touché. T13 pourra le remplacer par `classify`.
- `fake_data.DOMAINS` doit rester identique aux clés du YAML : un test le vérifie.

**Prochaine étape :**
- T7 (recruteurs LBA factices), **seulement après la fusion de la branche de Maxence** (T11), pour ne pas toucher `schemas.py` en même temps que lui.
- Formats à harmoniser avec Maxence (vus dans sa branche) : NAF `6201Z` (La bonne alternance) contre `62.01Z` (SIRENE et données factices), et taille en fourchette (`50-99`) contre codes INSEE de tranche d'effectif.

---

## 2026-11-27 — T5 : générateur de données factices ✅

**Fait :**
- `radar/fake_data.py` : génère, de façon reproductible (graine), **tous** les fichiers du contrat de `ARCHITECTURE.md` avec des entreprises inventées.
- `scripts/make_fake_data.py` : écrit les fichiers dans `data/`. Il refuse d'écraser des fichiers existants (de vraies données, peut-être) sans `--force`.
- `radar/schemas.py` : colonnes du contrat en code + `check_columns()`, utilisables par tout le monde (décision D7).
- `tests/test_fake_data.py` : 5 tests (schémas, SIRET valides, liens offres ↔ entreprises, une ligne par (siret, domaine), reproductibilité).
- Docs : D7 dans `DECISIONS.md` ; arborescence et emplacement des offres brutes dans `ARCHITECTURE.md` (j'ai aussi supprimé la ligne vide qui coupait le tableau des schémas) ; commande ajoutée dans `CLAUDE.md` › Stack ; T5 passée en « Fait ».

**Fichiers touchés :**
- `radar/fake_data.py`, `radar/schemas.py`, `scripts/make_fake_data.py`, `tests/test_fake_data.py`
- `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/TACHES.md`, `docs/journal/emma.md`

**Comment l'utiliser :**
```bash
uv run python scripts/make_fake_data.py          # 3 000 entreprises, graine 42 (≈ 6 s)
uv run python scripts/make_fake_data.py -n 10000 --seed 1 --force
```
```python
from radar.fake_data import generate      # tout en mémoire, sans écrire de fichier
data = generate(n_entreprises=500, seed=0) # data.entreprises, data.offres, data.scores…
```

**Résultats / chiffres clés (graine 42, 3 000 entreprises) :**
- 3 000 entreprises de ≥ 10 salariés autour de 24 villes (Paris 960, Lyon 261, Rennes 251…), dans 21 secteurs NAF ; SIRET et SIREN valides (clé de Luhn).
- 1 701 offres (1 514 Adzuna, 187 La bonne alternance) ; 23 % des entreprises ont au moins une offre (loi gamma-Poisson : beaucoup de zéros) ; 17 % des offres sont « data » ; 68 % emploi, 17 % stage, 15 % alternance.
- 80 % des offres Adzuna sont rapprochées d'un SIRET (méthode `nom_commune_fuzzy`) ; les offres La bonne alternance ont leur SIRET (`siret_source`).
- Domaine data : 180 entreprises recrutent dans la data, dont **142 sans offre de stage data** → des « opportunités cachées » à montrer dans l'app.
- `scores.parquet` : 15 000 lignes (3 000 × 5 domaines) ; `candidatures_simulees` : 3 000 lignes (taux de réponse 25 %) ; `p_reponse` : 30 000 lignes.
- Vérifié : `pytest` 7/7, ruff OK, l'app Streamlit charge les 3 000 entreprises sans erreur.

**Problèmes / points d'attention pour l'équipe :**
- ⚠️ **Tout est factice** : ne jamais montrer ces chiffres comme réels. Les descriptions portent `[DONNÉE FACTICE]` et les URL pointent vers `example.org`.
- Les formules de `scores`, `candidatures_simulees` et `p_reponse` sont **provisoires**, faites seulement pour avoir les bonnes colonnes : T30/T31 et T35/T36 (pas encore attribuées) les remplaceront.
- Domaines provisoires (`data, informatique, finance, marketing, rh` + `autre`) en attendant `domains.yaml` (T6). Codes ROME renseignés pour les offres data seulement (les codes de `SOURCES.md`) ; les autres domaines restent vides plutôt que d'inventer des codes.
- `data/` n'est pas dans Git : chacun lance le script sur son pod. T12 (@mathis) écrit aussi `data/raw/offres_raw/adzuna.parquet` : si son collecteur tourne sur un pod où le fichier factice existe déjà, il l'écrasera (c'est voulu). Dans l'autre sens, mon script refuse d'écraser ses vraies données.
- Colonnes en plus du contrat (permises) : `p_reponse.contrib_intensite`, `p_reponse.contrib_taille`, et `c_intensite` + `log_taille` dans `candidatures_simulees` (ce sont les `<variables>` du schéma).
- Relecture des docs (avant T5) : incohérences repérées et **non corrigées**, à trancher en équipe. Le passage de l'intensité « part des offres » (bêta-binomial) à « offres / effectif » (gamma-Poisson) après le test Adzuna n'est pas encore répercuté dans `PROJET.md`, `ARCHITECTURE.md` (modèle de score), ni dans l'ordre T31/T33. La colonne `lbb_proba` contient en réalité `hiring_potential` (un score, pas une probabilité). Le schéma de `ARCHITECTURE.md` parle encore de collecte « quotidienne » et de `scores_composantes.parquet`. D2 et `SOURCES.md` parlent encore de la Bretagne seule.

**Prochaine étape :**
- Proposer à l'équipe les corrections de docs ci-dessus, puis prendre T40 (page de recherche) ou T30 (score v0), qui sont débloquées par T5.

---

