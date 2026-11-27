# Journal — Emma

> Une entrée par session ou par tâche terminée, **la plus récente en haut**. Seule Emma écrit dans ce fichier.

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

