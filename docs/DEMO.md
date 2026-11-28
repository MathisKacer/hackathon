# Scénario de démo (T61) — 1 minute (dans un pitch de 3 minutes)

> Testé le 28/11 vers 06 h sur les données du jour (collecte Adzuna France entière, D50 ; poids 2 / 4, D48 bis). Les rangs peuvent bouger un peu si on relance `build_all.py` : **rejouer la minute en répétition (H+22), chronomètre en main**.

## Une seule idée à faire passer

**Les sites d'offres montrent les offres publiées ; Compass montre les entreprises qui ont un besoin data mais aucune offre visible.** Une recherche, une carte, une fiche. La méthode et la validation (AUC 0,92) sont dans les **diapos**, pas dans la démo.

## Avant de monter sur scène (checklist)

- [ ] `git pull`, `uv run python scripts/build_all.py` (~2 min), puis **redémarrer** Streamlit (recharger la page ne suffit pas).
- [ ] Faire la recherche Rennes une première fois (cache chaud : tout s'affiche en moins d'une seconde).
- [ ] Laisser l'appli sur la **page d'accueil**, avec **Rennes**, **Stage**, **Data**, **20 km** déjà remplis : la démo commence par un seul clic.
- [ ] Thème clair, zoom navigateur 110 %, notifications coupées.
- [ ] Vidéo de secours d'une minute (T62) prête dans un onglet.

## La minute

| Temps | Action | Ce qu'on dit (≈ 130 mots en tout) |
|---|---|---|
| 0:00 – 0:10 | Accueil déjà rempli → **Rechercher** | « Je suis à l'ENSAI, je cherche un stage data autour de Rennes. » |
| 0:10 – 0:25 | Montrer la carte, sans cliquer | « En bleu, les offres publiées : ce que tout le monde voit. En orange, ce que personne ne voit : des entreprises qui ont un besoin data, mais aucune offre de stage. Sur 4 000 entreprises autour de Rennes, Compass garde les meilleures cibles. » |
| 0:25 – 0:50 | Barre du haut › **Entreprises** → taper **Hellowork** → ouvrir la fiche du site de Rennes (●●● Cible prioritaire) | « Hellowork : aucune offre data publiée. Pourtant c'est une cible prioritaire : 250 à 499 salariés, dans un secteur qui recrute énormément de profils data. Chaque recommandation est expliquée en une phrase. » |
| 0:50 – 1:00 | Rester sur la fiche | « Une candidature spontanée bien ciblée, c'est une offre qu'on trouve avant qu'elle paraisse. » |

**Si la recherche Entreprises traîne** : fermer, onglet **Candidatures spontanées**, ouvrir la 1ʳᵉ ligne (**SPIKEELABS** : 6 offres d'emploi data, aucun stage) et dire « elle recrute en data, mais n'a jamais publié de stage ».

**Ce qu'on ne montre pas en démo** (trop long pour une minute, à garder pour les questions) : curseur de score de la carte, dépôt du CV et correspondance, favoris et suivi des candidatures, Lyon en alternance (EXALT LYON, 3ᵉ ; La Compagnie des animaux, ~80ᵉ, aucune offre data), France entière sans ville.

## Pour les diapos (les 2 minutes hors démo)

- **Validation, en une phrase** : « Calculé avec les seules offres d'avant le 13 novembre, notre classement place une entreprise qui a publié une offre data ensuite devant une qui n'a rien publié dans **92 % des cas**. »
- **Le LLM, en une phrase** : « Un LLM open source note les secteurs, jamais les entreprises ; ça améliore le score de façon significative. »
- **Phrase de fin** : « Compass ne remplace pas les sites d'offres : il montre les portes qui ne sont pas encore ouvertes. »

## Chiffres à avoir en tête (si le jury demande)

| Question | Réponse |
|---|---|
| Combien d'entreprises ? | ~277 000 établissements de 10 salariés et plus (SIRENE), France entière |
| Combien d'offres ? | ~15 600 offres data Adzuna (toutes les régions ; Île-de-France à 35 %) + ~12 700 de La bonne alternance |
| Le score ? | Modèle bayésien (Poisson) : offres data par salarié, rapprochées du profil de l'entreprise (taille, âge, capital, densité locale, **secteur noté par un LLM**). Puis besoin attendu = intensité × effectif. |
| Le LLM ? | Qwen 2.5 14B, open source. Il note les **secteurs** (718 codes NAF × 4 tailles), jamais une entreprise ; il ne crée aucune donnée. Il améliore le score de façon significative (+0,025 d'AUC face au même modèle sans secteur). |
| Validation ? | Coupure temporelle au 13/11 : AUC 0,92 (besoin caché), 0,95 (besoin futur). Meilleur que le même score en rangs (0,90) et qu'un GBM (0,89). Détails : `docs/EVAL_SCORE.md`. |
| « Chance de réponse » ? | Modèle entraîné sur des **réponses simulées** (il n'existe pas de données ouvertes de réponses) : on le dit toujours. |
| Limites ? | Offres Adzuna sur 60 jours seulement ; Île-de-France partielle ; un seul domaine noté (data) ; pas de LinkedIn ni de France Travail Offres (accès refusé). Voir `docs/LIMITES.md`. |
| RGPD ? | Données ouvertes uniquement ; aucun dirigeant affiché ; comptes facultatifs, mots de passe hachés. |

## Pièges à éviter

- **Ne pas montrer Guéret ou une petite ville** comme exemple : aucune cible prioritaire (c'est vrai, mais ça casse le rythme). Si le jury le demande, c'est une bonne réponse : « on ne fabrique pas de cibles là où il n'y a pas de besoin ».
- **Paris** : ~45 000 entreprises dans 20 km, plus lent à afficher et Île-de-France collectée à 35 %. Éviter en démo.
- **En alternance les scores plafonnent vers 0,8** : normal (le critère « recruteur d'alternants » vaut 0 pour la plupart des entreprises). Ne pas commenter le chiffre, commenter le palier.
- Un **score de 0,5 est déjà bon** (échelle logarithmique) : parler en **paliers** (« Cible prioritaire »), pas en nombre.
- Ne jamais dire « chance d'être embauché » : dire « priorité », « besoin estimé ».

## Plan B

- Réseau ou appli en panne → vidéo de secours d'une minute (T62), lancée sans commentaire de transition.
- Une entreprise citée ici a changé de rang → prendre la 1ʳᵉ ligne « ●●● Cible prioritaire » de la liste et lire sa phrase « Recommandée car… » : la démo ne dépend pas d'un nom précis.
