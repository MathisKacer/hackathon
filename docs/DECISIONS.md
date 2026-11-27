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
