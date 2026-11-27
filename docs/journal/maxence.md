# Journal — Maxence

> Une entrée par session ou par tâche terminée, **la plus récente en haut**. Seul son propriétaire écrit dedans.

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
