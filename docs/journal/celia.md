# Journal — Celia

> Une entrée par session ou par tâche terminée, **la plus récente en haut**. Seule Celia écrit dedans.

---

## 2026-11-27 — Tâche T20 : référentiel SIRENE France

**Fait :**
- `radar/collect/sirene.py` : DuckDB lit à distance les 3 stocks parquet SIRENE (établissements, unités légales, géolocalisation) et écrit `data/processed/entreprises.parquet`, conforme à `radar/schemas.py` (colonnes du contrat + colonnes utiles en plus, voir `ARCHITECTURE.md`).
- `radar/naf_rev2.csv` : libellés NAF rév. 2 (INSEE), avec une exception dans le `.gitignore`.
- `tests/test_sirene.py` : table NAF, tranches, requête valide (sans réseau), contrat respecté si le fichier existe.
- Décision D10 (D8 et D9 étaient déjà pris par Mathis et Emma).

**Fichiers touchés :**
- `radar/collect/sirene.py`, `radar/naf_rev2.csv`, `tests/test_sirene.py`, `.gitignore`, `CLAUDE.md` (une commande), `docs/*`

**Résultats / chiffres clés :**
- 406 266 établissements actifs ≥ 10 salariés, 278 950 entreprises, 101 départements ; 99,7 % géolocalisés ; 0 % sans nom ; 100 % avec libellé NAF ; 19 Mo ; 39 s.
- Effectifs : tous de 2024. Catégories : 245 k PME, 96 k ETI, 61 k GE.
- Ille-et-Vilaine (35) : 7 514 établissements.

**Problèmes / points d'attention pour l'équipe :**
- Chacun peut régénérer le fichier : `uv run python -m radar.collect.sirene` (option `--dep 35` pour tester).
- `ca_n`, `ca_n_1`, `lbb_proba` sont vides et `procedure_collective` vaut `False` : à remplir par T22, T24 et T23.
- `.gitignore` : ajout de l'exception `!radar/naf_rev2.csv`.
- ⚠️ `uv run ruff format .` reformate aussi les blocs Python **dans les fichiers Markdown** (dont les journaux des autres) : vérifier son `git diff` avant de committer.

**Prochaine étape :**
- T21 (rapprochement nom + commune → SIRET) peut s'appuyer sur `nom`, `nom_entreprise`, `sigle`, `code_postal`, `code_commune`.
