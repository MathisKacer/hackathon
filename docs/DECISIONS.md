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

### D1 — Coordination via fichiers Markdown dans le dépôt (2026-11-27, @mathis)
**Contexte :** plusieurs personnes, chacune avec sa propre session Claude Code, sur le même dépôt.
**Décision :** `CLAUDE.md` comme règles communes ; `docs/TACHES.md` pour se répartir le travail ; un journal par personne dans `docs/journal/` pour éviter les conflits Git.
**Alternatives écartées :** un seul fichier d'avancement partagé (conflits de merge permanents).
**Conséquences :** chaque session suit le rituel décrit dans `CLAUDE.md`.
