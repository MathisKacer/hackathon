# Scénario de démo (T61) — 5 minutes

> Testé le 28/11 vers 06 h sur les données du jour (collecte Adzuna France entière, D50 ; poids 2 / 4, D48 bis). Les rangs et les scores ci-dessous peuvent bouger un peu si on relance `build_all.py` : **refaire un passage complet en répétition (H+22)** et corriger ce fichier si besoin.

## Le fil rouge

Une étudiante de l'ENSAI cherche un **stage data à Rennes**. Les sites d'offres lui montrent les offres publiées ; **Compass lui montre en plus les entreprises qui ont un besoin data mais pas d'offre de stage visible**, classées par un score qu'on sait expliquer et qu'on a validé.

Trois idées à faire passer, une par acte :
1. **Les deux couches** : 🔵 offres réelles, 🟠 candidatures spontanées.
2. **Pourquoi cette entreprise** : chaque recommandation est expliquée en une phrase.
3. **Ça marche ailleurs et ça se valide** : hors Bretagne, et une validation sur des offres « futures ».

## Avant de commencer (checklist)

- [ ] `git pull`, puis `uv run python scripts/build_all.py` (~2 min), puis **redémarrer** Streamlit (recharger la page ne suffit pas).
- [ ] Ouvrir l'appli, faire une recherche Rennes une première fois (met les données en cache : la démo sera fluide).
- [ ] Un **compte de démo** déjà créé (identifiant et mot de passe partagés en message privé, jamais dans le dépôt).
- [ ] Un **CV PDF** de démo sur le bureau, avec Python, SQL, machine learning.
- [ ] Thème clair (lisible au vidéoprojecteur), zoom navigateur à 110 %.
- [ ] Vidéo de secours (T62) prête dans un onglet.

## Acte 1 — La recherche (≈ 1 min 30)

| Action | Ce qu'on dit |
|---|---|
| Page d'accueil : **Rennes**, contrat **Stage**, domaine **Data**, rayon **20 km** → **Rechercher** | « Je suis en M2 à l'ENSAI, je cherche un stage data autour de Rennes. » |
| Montrer la carte : points **bleus** et **orange** | « En bleu, les offres publiées : ce que tout le monde voit. En orange, ce que personne ne voit : des entreprises qui ont un besoin data, mais **aucune offre de stage**. » |
| Lire la légende sous la carte : « ~135 entreprises sur la carte (meilleures cibles) sur ~4 300 » | « Il y a plus de 4 000 sites d'entreprises dans le rayon. On n'en montre que les meilleures cibles, et la liste garde tout. » |
| Filtres › Classement › curseur **« Score minimal sur la carte »** : passer à **≥ 0,80** puis revenir à **Auto** | « L'étudiante choisit combien elle en veut. » |

## Acte 2 — Pourquoi cette entreprise ? (≈ 2 min)

| Action | Ce qu'on dit |
|---|---|
| Onglet **Candidatures spontanées** : la 1ʳᵉ ligne est **SPIKEELABS** (●●● Cible prioritaire) → ouvrir la **fiche** | « Premier cas : l'**opportunité cachée**. Elle publie 6 offres d'emploi data, mais aucun stage. Elle a le besoin, elle n'a juste pas pensé à un stagiaire. » Lire la phrase « Recommandée car… ». |
| Page **Entreprises** (barre du haut) : chercher **Hellowork** → fiche du site de Rennes (●●● Cible prioritaire) | « Deuxième cas, le plus fort : **aucune offre data du tout**. Mais 250 à 499 salariés dans un secteur qui recrute énormément de profils data. Notre modèle estime son besoin d'après les entreprises qui lui ressemblent. » |
| Revenir à la liste : montrer **IFIP – Institut du porc** (Pacé, ~24ᵉ) ou **MGEN** (Cesson-Sévigné, ~33ᵉ) | « Et pas seulement des ESN : la recherche agronomique, l'assurance… des endroits où on n'aurait pas pensé à candidater. » |
| Filtres › **Ton CV** : déposer le CV de démo → colonne **Correspondance** | « Si je dépose mon CV, Compass compare mes compétences à celles que demande le secteur. Ça ne change pas le score : c'est une information en plus. » |
| Cliquer ⭐ (favori) sur une fiche, puis **Mon compte** → Candidatures : statut « Envoyée », rappel de relance à 15 jours | « Je suis mes candidatures, Compass me rappelle de relancer. » (Se connecter avec le compte de démo juste avant, ou montrer que les favoris sont gardés à la connexion.) |

## Acte 3 — Hors Bretagne, et est-ce que ça marche ? (≈ 1 min 30)

| Action | Ce qu'on dit |
|---|---|
| Changer la ville : **Lyon**, contrat **Alternance** | « Toute la France est couverte : on a collecté les offres de toutes les régions. » |
| Ouvrir **EXALT LYON** (3ᵉ) ou **La Compagnie des animaux** (~80ᵉ, aucune offre data, 100–199 salariés) | Même lecture que l'acte 2, en une phrase. |
| Diapo **validation** (pas dans l'appli) | « On a vérifié le score sans tricher. On l'a calculé avec les offres publiées **avant le 13 novembre** seulement, puis on a regardé quelles entreprises ont publié une offre data **après**. Le classement que voit l'étudiant place une entreprise qui a publié ensuite devant une qui n'a rien publié **dans 92 % des cas** (AUC 0,92), et 95 % sur l'ensemble des entreprises. » |

**Phrase de fin :** « Compass ne remplace pas les sites d'offres : il montre les portes qui ne sont pas encore ouvertes. »

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

- Réseau ou appli en panne → vidéo de secours (T62).
- Une entreprise citée ici a changé de rang → prendre la 1ʳᵉ ligne « ●●● Cible prioritaire » de la liste et lire sa phrase « Recommandée car… » : la démo ne dépend pas d'un nom précis.
