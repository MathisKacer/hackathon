# Piste : domaines de recrutement de chaque entreprise par un LLM (secteur × taille)

> Note de passation rédigée par @emma (2026-11-27) pour que @mathis reprenne le sujet. **Rien n'est décidé ni lancé** : c'est une proposition qui rouvre D21 (reportée) et touche `radar/score/build.py`. Il faut l'accord de l'équipe avant de coder. Tâche : T77.

## 1. L'objectif

Ce qu'on veut vraiment (reformulation d'Emma) : pour **chaque entreprise**, savoir si elle **peut recruter dans le domaine recherché**, compte tenu de sa situation. C'est la base de la candidature spontanée. Recenser les offres reste utile, mais c'est secondaire.

- Une entreprise peut recruter dans **plusieurs domaines**. Exemple : une banque recrute en data, en finance et en RH.
- On n'a **pas de données de validation** pour l'instant (de vraies réponses à des candidatures). C'est assumé : on veut une application **qu'on peut montrer**, pas un modèle fini et généralisable.
- Ce qui compte : que le modèle soit **fiable sur les domaines où une entreprise peut recruter**.

Modèle proposé :

```
score(entreprise, domaine) = besoin dans le domaine  ×  capacité à recruter
                             (dépend du domaine)        (ne dépend pas du domaine)
```

- **Besoin dans le domaine** : a priori par secteur (NAF) × taille, **donné par un LLM** (section 3), corrigé par les offres observées de l'entreprise quand il y en a (le modèle actuel de @mathis, D33).
- **Capacité à recruter** : ce qu'on a déjà, commun à tous les domaines : BODACC (D24), taille, potentiel d'embauche global de La Bonne Boîte (`c_embauche`, D27), proximité.

## 2. Ce qui a été testé et écarté (sources ouvertes)

| Source | Résultat | Verdict |
|---|---|---|
| **Enquête BMO** (France Travail, fichiers ouverts 2024 et 2026) | Intentions d'embauche par **métier (FAP) × bassin d'emploi** uniquement : **pas de dimension secteur**, et pas de métier « data » séparé | ❌ inutilisable comme a priori par secteur |
| **La Bonne Boîte, finance** (T74, 253 appels, 20 611 établissements) | Le NAF seul retrouve les établissements signalés avec une AUC de **0,97** (taille seule 0,61). Mais 247 des 315 gros NAF n'ont **aucun** établissement signalé (gestion de fonds : 0/636), banques 9 % seulement, jeux de hasard 75 % | ❌ le domaine vient d'une correspondance NAF ↔ métier, pas d'embauches observées. Détails : `SOURCES.md` (ligne La Bonne Boîte), journal d'Emma |
| **Recruteurs potentiels LBA** (codes ROME par recruteur) | Même logique : métiers déduits du secteur (L26). AUC 0,66 pour retrouver les signalés finance de LBB | ❌ pas un signal propre à l'entreprise |

Deux conséquences :
1. En données ouvertes, le seul signal **propre à une entreprise et à un domaine**, ce sont **ses offres** (d'où l'intérêt de bien les classer : T68).
2. `c_embauche` (T28, D27) mesure une **capacité d'embauche générale**, pas un besoin data. Il reste valable dans le « × capacité à recruter », mais il ne faut pas le présenter comme une preuve de besoin data.

## 3. La proposition : une grille secteur × taille × domaine remplie par un LLM

Pourquoi un LLM plutôt que les offres pour l'a priori : les offres ne sont pas fiables non plus (requête Adzuna « data » bruitée, 36,6 % des offres Adzuna et 92,8 % des offres LBA en `autre`, L25). Un LLM « sait » quels métiers emploie un secteur selon sa taille (une banque de 1 000 salariés a une équipe data ; une boulangerie de 15 salariés non). Choix d'Emma : **tout passer par le LLM** pour l'a priori.

**Unité** : le code NAF (718 codes présents dans `entreprises.parquet`) × les 4 classes de taille de l'app (`radar/filters.py › TAILLES` : 10–49, 50–249, 250–999, 1 000 et plus) × les 5 domaines de `domains.yaml` (data, informatique, finance, marketing, rh).

- 718 × 4 × 5 = **14 360 cases**. On ne demande pas case par case : **une question par NAF** (ou par paquet de 10 NAF), qui renvoie sa grille 4 tailles × 5 domaines.
- Pourquoi pas les 11 tranches SIRENE : 4 199 combinaisons NAF × tranche non vides, trop fin pour que le LLM distingue quelque chose. Avec 4 classes : 2 071 combinaisons non vides (674 NAF couvrent 95 % des établissements).
- Repli possible si besoin : la division NAF (88) × 4 tailles = 313 combinaisons non vides.

**Échelle** (0–3), avec une justification courte par domaine :

| Note | Sens | Exemple |
|---|---|---|
| 0 | jamais ou presque | data dans une boulangerie de 10–49 salariés |
| 1 | rare | RH dans une PME industrielle de 10–49 |
| 2 | courant | finance dans une ETI industrielle |
| 3 | cœur de métier / équipe dédiée | data dans une ESN, finance dans une banque |

**Brouillon de consigne** (à affiner) :

```text
Tu es un expert du marché du travail français. Pour le secteur d'activité ci-dessous (code NAF
rév. 2 et libellé), indique pour chaque taille d'établissement si une entreprise de ce secteur
recrute habituellement dans chacun des 5 domaines (stage, alternance ou emploi).
Domaines : data (data, statistique, IA) ; informatique (développement, systèmes d'information) ;
finance (comptabilité, contrôle de gestion, banque) ; marketing (marketing, communication,
études commerciales) ; rh (ressources humaines).
Tailles : "10-49", "50-249", "250-999", "1000+" salariés.
Note : 0 = jamais ou presque, 1 = rare, 2 = courant, 3 = cœur de métier ou équipe dédiée.
Réponds uniquement en JSON :
{"naf": "...", "grille": {"10-49": {"data": n, ...}, ...}, "justification": {"data": "...", ...}}
Secteur : {naf} — {naf_libelle}
```

**Précautions** (à garder, ce sont elles qui rendent le résultat défendable au pitch) :
- **Température 0 + consigne versionnée dans le dépôt + résultat en cache** (`data/processed/…`, hors Git) : même entrée → même grille, relances gratuites.
- **Sortie contrôlée** : JSON validé (5 domaines, 4 tailles, notes 0–3), sinon on relance ; NAF manquant → note moyenne du domaine.
- **Relecture d'un échantillon d'environ 50 secteurs** par l'équipe (les plus fréquents + quelques cas limites) : taux d'accord à mettre dans les slides.
- **Contrôle de cohérence avec les offres** : là où on a des offres (data surtout), les secteurs notés 3 doivent avoir plus d'offres du domaine que ceux notés 0 (AUC ou corrélation de rang).
- Dans l'app : présenter la note comme « **d'après le secteur et la taille** », jamais comme une embauche observée.
- Le LLM **qualifie des secteurs réels**, il ne crée aucune donnée d'entreprise (même règle que T68).

## 4. Moyens de calcul : ce qu'on a vérifié

- Le pod d'Emma : 128 cœurs, ~1 To de RAM, **pas de carte graphique** (`nvidia-smi` absent). La variable `ANTHROPIC_API_KEY` existe dans `.env.example` mais **n'est pas remplie** dans le `.env` d'Emma (vérifié sans afficher le contenu).
- **Volume** : avec des paquets de 10 NAF, ~72 appels, ~175 000 tokens (≈ 250 000 avec la marge des relances).

| Option | Temps estimé | Remarques |
|---|---|---|
| **API commerciale** (clé Anthropic ou autre) | ~10–20 min | Meilleure connaissance des secteurs ; coût faible pour ~250 000 tokens ; il faut une clé (personne n'en a pour l'instant) |
| **Abonnement Claude Pro** (sessions Claude Code) | Possible en plusieurs fois | ~250 000 tokens tiennent dans les quotas en étalant, mais pas industrialisable ni reproductible par script ; à éviter sauf dépannage |
| **LLM open source sur CPU** (Ollama, 7B) | **~3 h** | La génération est limitée par la vitesse de la mémoire, pas par le nombre de cœurs : ~5–20 tokens/s |
| **LLM open source sur GPU** (vLLM) | quelques minutes à ~20 min, + 20–40 min d'installation | **Option préférée si on obtient une carte** : gratuit, sans clé, reproductible (modèle ouvert + consigne + température 0), les données restent sur le SSP Cloud |

Modèle selon la mémoire de la carte : ~16 Go → 7–8 milliards de paramètres (Qwen 2.5 7B, Mistral 7B, Llama 3.1 8B) ; 24–48 Go → 14–24 milliards compressés (Qwen 2.5 14B, Mistral Small 24B) ; 80 Go → 30–70 milliards compressés, qualité proche d'une API. Viser **≥ 14 milliards** si possible. Une carte Onyxia est souvent partagée ou limitée dans le temps : tout préparer avant (liste des NAF, consigne, script), lancer, libérer.

## 5. Branchement dans le score (à décider avec @mathis)

Rien n'est codé. Pistes :
- `SCORED_DOMAINS` = les 5 domaines (fin de D21 « reportée »), une ligne par `siret × domaine` comme aujourd'hui.
- La note LLM (NAF × taille) entre dans le modèle de D33 comme **covariable ou a priori sectoriel**, à la place ou à côté de l'a priori NAF estimé sur les offres. Pour data, on peut comparer les deux (le score v1 a déjà un a priori NAF hiérarchique : voir si la note LLM l'améliore sur `docs/EVAL_SCORE.md`).
- Hors data, peu ou pas d'offres → le score repose surtout sur la note LLM × capacité à recruter. Afficher « signal partiel » (déjà prévu par D21).
- Affichage : dans la fiche, « Domaines où ce secteur recrute d'habitude : data ●●●, finance ●●○… » permettrait de montrer le « plusieurs domaines par entreprise ».

## 6. Ce qu'il reste à faire

1. **Décision d'équipe** : rouvrir D21 avec cette méthode ? Si oui, nouvelle entrée Dxx dans `DECISIONS.md`.
2. **Trouver le calcul** : carte graphique Onyxia (donner le résultat de `nvidia-smi` pour choisir le modèle) ou clé d'API.
3. Préparer (sans rien lancer) : la liste des 718 NAF avec libellés et nombre d'établissements, la consigne versionnée, un script compatible vLLM et Ollama (API compatible OpenAI) avec cache et validation du JSON.
4. Lancer, relire l'échantillon, contrôler la cohérence avec les offres.
5. Brancher dans `radar/score/build.py` (@mathis) et l'afficher dans l'app (fiche, couche 🟠 pour les autres domaines).
