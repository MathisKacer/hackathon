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
- Ne pas committer de notebooks avec des sorties volumineuses (vider les sorties avant commit).

## Stack et commandes

> À compléter dès que la stack est choisie (langage, gestionnaire de dépendances, commandes pour installer / lancer / tester).

```bash
# installer :  TBD
# lancer :     TBD
# tester :     TBD
```

## Style de réponse attendu de Claude

- Répondre en français.
- Code et noms de variables en anglais ou français, mais **cohérents** avec l'existant (voir `docs/ARCHITECTURE.md` › Conventions).
- C'est un hackathon : privilégier ce qui marche et se démontre vite, mais garder le code lisible pour les coéquipiers.
