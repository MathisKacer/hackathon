# Scénario de démo (T61, T62) — vidéo d'1 minute, **enregistrée à l'avance** (pitch de 3 minutes)

> Testé le 28/11 vers 06 h sur les données du jour (collecte Adzuna France entière, D50 ; poids 2 / 4, D48 bis). Les rangs peuvent bouger un peu si on relance `build_all.py` : **vérifier les noms juste avant d'enregistrer**.

## Une seule idée à faire passer

**Les sites d'offres montrent les offres publiées ; Compass montre les entreprises qui ont un besoin data mais aucune offre visible.** Une recherche, une carte, une fiche. La méthode et la validation (AUC 0,92) sont dans les **diapos**, pas dans la démo.

## Principe

La démo est **toujours une vidéo enregistrée à l'avance**, jamais l'appli en direct : aucun risque de réseau, de lenteur ou de clic raté, et la durée est garantie.

- **Vidéo sans son, commentée en direct** par l'orateur (recommandé) : le texte ci-dessous est calé sur les images ; on garde l'énergie du direct et on peut ralentir ou accélérer la voix.
- Garder aussi une **version avec voix off** (même vidéo, texte enregistré) au cas où l'orateur préfère ne pas parler par-dessus.

## Préparer l'enregistrement (checklist)

- [ ] `git pull`, `uv run python scripts/build_all.py` (~2 min), puis **redémarrer** Streamlit (recharger la page ne suffit pas).
- [ ] Faire la recherche Rennes une première fois (cache chaud : tout s'affiche en moins d'une seconde).
- [ ] Navigateur **propre** : fenêtre seule, plein écran (F11), sans barre de favoris ni autres onglets, zoom 110 %, thème clair, notifications coupées.
- [ ] Remplir l'accueil : **Rennes**, **Stage**, **Data**, **20 km** ; la vidéo commence sur cet écran.
- [ ] Souris lente et visible ; ne rien survoler d'inutile.

## Enregistrer

**Automatique (recommandé)** : `scripts/demo_video.py` pilote un navigateur sans écran sur le pod et produit `data/demo/demo.mp4` (55 s, 1080p, H.264, muette, curseur visible). L'appli doit tourner sur le port 8501.

```bash
uv run --with playwright playwright install chromium        # une fois par pod
uv run --with playwright playwright install-deps chromium   # une fois par pod (sudo)
uv run --with playwright --with imageio-ffmpeg python scripts/demo_video.py
# --essai : captures d'écran de chaque étape ; --pause-carte / --pause-fiche : caler sur l'orateur
```

Récupérer la vidéo : clic droit sur `data/demo/demo.mp4` dans l'explorateur de VS Code › Download.

**À la main** (si besoin) :

- **Outil** : Windows `Win + G` (Xbox Game Bar) ou `Win + Alt + R` ; macOS `Cmd + Shift + 5` ; ou OBS Studio. Enregistrer **la fenêtre du navigateur seule**, en **1080p**, MP4.
- Faire **3 ou 4 prises** en lisant le texte à voix haute pour le rythme, garder la meilleure.
- **Montage minimal** (Clipchamp sous Windows, iMovie sous macOS, ou l'éditeur de Canva) : couper le début et la fin, accélérer les attentes (frappe de « Hellowork », chargement), viser **55 à 60 s**. Facultatif : un zoom sur la phrase « Recommandée car… » de la fiche.
- **Où la mettre** : intégrée dans la diapo de démo (lecture automatique) **et** en fichier MP4 à part (clé USB + Drive de l'équipe). Ne pas la mettre dans le dépôt Git.
- Après l'enregistrement : la regarder une fois en entier sur l'ordinateur de présentation, avec le vidéoprojecteur si possible.

## La minute (texte calé sur la vidéo)

| Temps | Action | Ce qu'on dit (≈ 130 mots en tout) |
|---|---|---|
| 0:00 – 0:05 | Accueil déjà rempli → **Rechercher** | « Je suis à l'ENSAI, je cherche un stage data autour de Rennes. » |
| 0:05 – 0:24 | La carte s'affiche, le curseur survole un point orange (info-bulle « Cible prioritaire ») | « En bleu, les offres publiées : ce que tout le monde voit. En orange, ce que personne ne voit : des entreprises qui ont un besoin data, mais aucune offre de stage. Sur 4 000 entreprises autour de Rennes, Compass garde les meilleures cibles. » |
| 0:24 – 0:45 | Barre du haut › **Entreprises** → **Hellowork**, Rennes → fiche du site de Rennes (●●● Cible prioritaire) | « Hellowork : aucune offre data publiée. Pourtant c'est une cible prioritaire : 250 à 499 salariés, dans un secteur qui recrute énormément de profils data. Chaque recommandation est expliquée en une phrase. » |
| 0:45 – 0:55 | Fiche : décomposition du score, « aucune offre du domaine observée » | « Une candidature spontanée bien ciblée, c'est une offre qu'on trouve avant qu'elle paraisse. » |

**Variante si Hellowork n'est plus en « Cible prioritaire »** au moment d'enregistrer : onglet **Candidatures spontanées**, ouvrir la 1ʳᵉ ligne (**SPIKEELABS** : 6 offres d'emploi data, aucun stage) et dire « elle recrute en data, mais n'a jamais publié de stage ».

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
- **Paris** : ~45 000 entreprises dans 20 km et Île-de-France collectée à 35 %. Ne pas l'utiliser dans la vidéo.
- **En alternance les scores plafonnent vers 0,8** : normal (le critère « recruteur d'alternants » vaut 0 pour la plupart des entreprises). Ne pas commenter le chiffre, commenter le palier.
- Un **score de 0,5 est déjà bon** (échelle logarithmique) : parler en **paliers** (« Cible prioritaire »), pas en nombre.
- Ne jamais dire « chance d'être embauché » : dire « priorité », « besoin estimé ».

## Plan B

- La vidéo ne se lance pas depuis les diapos → ouvrir le fichier MP4 directement (clé USB ou Drive).
- Aucune vidéo possible → une diapo avec 3 captures (carte, liste, fiche Hellowork) et le même texte.
- Une entreprise citée ici a changé de rang avant l'enregistrement → prendre la 1ʳᵉ ligne « ●●● Cible prioritaire » de la liste et lire sa phrase « Recommandée car… » : la démo ne dépend pas d'un nom précis.
