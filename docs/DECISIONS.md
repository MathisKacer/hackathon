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

### D32 — Score en paliers de priorité, règle mixte (rang dans la recherche + score minimal) (2026-11-27, @maxence)
**Contexte :** T65 : afficher le score en mots et en couleurs. Le score est une moyenne pondérée de **rangs centiles** (D13, D22) : il n'est pas une probabilité, il dépend des curseurs, et il est plus bas en alternance (composante LBA souvent nulle) et en zone rurale.
**Décision :** `radar/paliers.py`, 4 paliers. Une entreprise atteint un palier si elle est **à la fois** parmi les meilleures **de la recherche affichée** (part des résultats classés devant elle, ex æquo traités ensemble et prudemment) **et** au-dessus d'un score minimal :
| Palier | Repère | Condition |
|---|---|---|
| Cible prioritaire | ●●● orange foncé | 10 % meilleures et score ≥ 0,60 |
| Bonne cible | ●●○ orange | 30 % meilleures et score ≥ 0,45 |
| À considérer | ●○○ orange clair | 60 % meilleures et score ≥ 0,30 |
| Moins indiquée | ○○○ gris | les autres |
Seuils calibrés sur Rennes, Lyon et Guéret (5 et 20 km, stage et alternance, poids par défaut) : le palier 1 ≈ les 10 % meilleures ; le minimum ne bloque que dans les recherches faibles (Guéret alternance). Libellés de **priorité**, jamais de probabilité (« probable » écarté : confusion avec la chance de réponse simulée, D23/D31). Les points (●●○) servent de repère sans couleur (daltonisme). Le **score reste affiché** : colonne à côté de la priorité, info-bulle et fiche de la carte, sous la priorité dans la fiche.
**Alternatives écartées :** seuils fixes seuls (presque jamais de palier haut en alternance ou en zone rurale) ; quantiles seuls (une entreprise moyenne de Guéret annoncée « prioritaire ») ; libellés « Possible / Probable / Fortement probable » proposés dans la tâche.
**Complément (demande de Maxence) :** en plus des 4 couleurs de palier, un **dégradé continu d'orange** (clair → foncé, `score_color`) : fond de la colonne « Score » de la liste (score brut, 0 à 1) et remplissage des points de la carte. Sur la carte, le dégradé est **étalé entre le plus faible et le plus fort score affichés** : en ville, les 300 points montrés ont tous un score de 0,8 à 1 et seraient sinon de la même couleur. La taille des points suit toujours le palier.
**Conséquences :** le palier d'une entreprise dépend de la recherche (zone, filtres, poids) : c'est voulu, il dit « par où commencer ici ». Si T69 change la distribution du score, revoir les seuils minimaux (constantes `TIERS`).

---

### D31 — « Chance de réponse » : libellé clair, mention « simulée » en info-bulle (2026-11-27, @celia)
**Contexte :** T64. L'app affichait « P(réponse) simulée », peu clair pour un étudiant, avec un bandeau « Démonstration » et « (démo) » dans les libellés ; la colonne n'apparaissait que si l'on classait par chance de réponse.
**Décision :** libellé **« Chance de réponse »** partout (liste, fenêtre de la carte, fiche, classement dans « Filtres ») ; colonne toujours affichée quand le modèle couvre le contrat et le domaine. **Précise D6 / D23 sur l'affichage** : plus de bandeau ni de « (démo) » à l'écran ; la mention « modèle entraîné sur des réponses simulées » reste dans les **info-bulles** de la colonne et de la fiche (`CHANCE_HELP`, `app/commun.py`) et sera **dite au pitch**.
**Alternatives écartées :** garder le bandeau (alourdit l'écran, choix de l'équipe) ; supprimer toute mention (une estimation simulée présentée comme une vraie statistique induirait en erreur un utilisateur réel).
**Conséquences :** au pitch et dans les slides, dire clairement que les chances de réponse viennent de réponses simulées (D6). Les profils enregistrés avec l'ancien libellé de classement reviennent au classement par score.

### D30 — Interface en 3 pages, épurée (2026-11-27, @celia)
**Contexte :** la barre latérale cumulait compte, 13 réglages et 5 curseurs ; les textes montraient du jargon interne (numéros de tâches, fichiers, commandes) et beaucoup d'emojis ; l'idée centrale n'était expliquée qu'en bas de la barre latérale.
**Décision :** navigation en haut avec 3 pages (`st.navigation`) : **Explorer** (recherche en haut : ville, contrat, domaine, rayon ; le reste dans un panneau « Filtres » ; phrase de résultat ; carte ; onglets « Candidatures spontanées » / « Offres » ; clic sur une ligne → fiche dans une fenêtre `st.dialog`), **Entreprises** (barre de recherche sur les ~406 000 établissements, tolérante aux fautes, `radar/recherche.py`), **Mon espace** (compte, profil, historique avec « Relancer »). Code de la carte déplacé **sans modification** dans `app/carte.py`. Réglages conservés entre les pages (`persist_widget_state`). Thème sobre (`.streamlit/config.toml` : bleu nuit, police Inter) qui laisse au bleu et à l'orange de la carte leur sens. On garde les mots « Candidatures spontanées » et « Offres ».
**Alternatives écartées :** une seule page avec recherche d'entreprises intégrée (moins lisible) ; fiche sous la liste (on la perdait de vue).
**Conséquences :** nouvelle consigne pour les réglages dans `CLAUDE.md` (`WIDGET_KEYS`, `profile_keys()`, `init_defaults()` dans `app/commun.py`). Commande de lancement inchangée.

### D29 — Explication « Recommandée car … » (2026-11-27, @mathis)
**Contexte :** T32. Le jury et l'étudiant doivent comprendre pourquoi une entreprise est proposée en candidature spontanée, sans lire une décomposition chiffrée.
**Décision :** `radar/explain.py`, fonction pure `explain(ligne, contrat)`. Raisons candidates tirées des colonnes existantes : **opportunité cachée** (offres du domaine en ligne mais aucune pour le contrat visé, détaillées par type de contrat), **La Bonne Boîte**, **recruteur d'alternants LBA**, **besoin du secteur / de l'entreprise** (rang centile de `c_intensite`), **taille de l'établissement**, **proximité** (≤ 5 km). L'opportunité cachée vient toujours en premier (c'est la raison d'être de la couche orange), puis les **signaux externes vérifiables** (La Bonne Boîte, recruteur La bonne alternance : sinon la limite de 3 raisons les écartait au profit de rangs centiles, constaté sur les vraies données LBA), puis les autres **par apport au score** (`apport_<composante>`, donc cohérent avec les curseurs T42) ; 3 raisons maximum, plus une mise en garde si `couverture = 0`. Branchée par une ligne en fin de `rank_spontaneous` (colonne `explication`, lue par la fiche T43 et le popup de la carte), pour les **1 000 premières** entreprises seulement.
**Alternatives écartées :** une phrase générée par un LLM (pas de clé, non reproductible, risque d'invention) ; précalculer dans `scores.parquet` (la phrase dépend du contrat, de la distance et des poids de l'utilisateur) ; expliquer toutes les lignes (Paris 50 km : 77 000 entreprises, 4 s par clic au lieu de 0,9 s).
**Conséquences :** au-delà du 1 000e rang, `explication` est vide (la fiche affiche la décomposition) ; `explain(ligne)` peut être appelée à la demande. Ajouter une composante au score (T42) = ajouter sa raison dans `reasons()`.

### D28 — Suggesteur de ville : liste « Ville (code postal) » au lieu d'une adresse libre (2026-11-27, @maxence)
**Contexte :** T55 : avec une adresse libre, une faute de frappe ou un homonyme (« Saint-Martin ») donnait un mauvais lieu ou « adresse introuvable ». On veut taper le nom de la ville et la **valider dans une liste déroulante** avec son code postal.
**Décision :** `radar/communes.py`. Liste de **toutes les communes** via l'API Découpage administratif (geo.api.gouv.fr, sans clé) : **un seul appel** (≈ 4,8 Mo) gardé 30 jours dans le cache disque, **une ligne par commune** avec tous ses codes postaux = 34 964 choix, libellé « Nom (CP1, CP2…) » (ex. « Rennes (35000, 35200, 35700) », on peut aussi taper un code postal ; révisé à la demande de Maxence, au départ une ligne par code postal), triés par population (les grandes villes sortent en premier). Dans l'app, un `st.selectbox` où l'on **tape pour filtrer** (natif dans Streamlit), créé avec `index=None` : c'est ce qui affiche la **croix pour effacer** la ville (sans elle, impossible de revenir à vide), clé `ville` dans le profil (options = les libellés). Point de départ = **centre de la commune**. Réseau coupé → repli sur les communes du référentiel entreprises.
**Alternatives écartées :** champ texte + liste de suggestions recalculée à chaque frappe via l'API de complétion de la Géoplateforme (un appel réseau par recherche et deux widgets à manipuler) ; garder l'adresse à la rue (précision inutile pour un rayon de 5 à 100 km, et source d'erreurs).
**Conséquences :** l'ancienne clé de profil `adresse` disparaît (profils enregistrés : il faut rechoisir sa ville une fois). Paris, Lyon et Marseille : un seul centre pour tous les arrondissements. `radar/geocode.py` reste disponible mais l'app ne l'utilise plus.

---

### D27 — `c_embauche` : La Bonne Boîte d'abord, proxy ensuite (2026-11-27, @emma)
**Contexte :** T28 / L11. `c_embauche` était un proxy (intensité data × effectif local, D13) qui favorise les gros établissements. La Bonne Boîte v2 donne un vrai `hiring_potential` par SIRET et par métier, fondé sur les déclarations d'embauche. Mais pour les métiers data, elle ne connaît que 1 736 établissements en France (1 331 dans notre référentiel de 406 266, soit 0,3 %).
**Décision :** `radar/score/embauche.py`. Un établissement signalé par La Bonne Boîte pour un code ROME **non ambigu** du domaine passe **devant** tous les autres (être listé est un signal d'embauche en soi), et ces établissements sont classés entre eux par `lbb_potentiel` (max sur les métiers). Les autres gardent l'ordre du proxy, dans la partie basse de l'échelle, dont la taille est la part d'établissements sans La Bonne Boîte. `c_embauche_source` indique la source ligne par ligne, et `lbb_potentiel` garde la valeur brute (pour la fiche entreprise). Collecte : `scripts/collect_lbb.py` (30 appels, cache disque), puis `build_all.py`. Sans `data/raw/lbb.parquet`, le comportement d'avant est conservé (proxy seul, avertissement).
**Alternatives écartées :** La Bonne Boîte seule (99,7 % des établissements sans valeur) ; mélanger les deux sources dans un même rang (une valeur La Bonne Boîte et un proxy ne sont pas sur la même échelle) ; ajouter les recruteurs LBA à `c_embauche` (déjà comptés par `c_recruteur_lba`, D26 : double comptage) ; utiliser le drapeau `is_high_potential` (vrai pour 1 établissement sur 1 736).
**Conséquences :** il faut relancer `collect_lbb.py` puis `build_all.py` sur le pod qui produit les scores (@mathis). Le modèle de réponse simulé (T36), qui utilise `c_embauche`, change aussi au prochain `build_all`. Dans l'app et les slides, on peut dire « signalée par La Bonne Boîte (France Travail) » pour ces établissements. Limite restante : couverture faible, voir L11.

### D26 — Recruteurs LBA : composante « Recruteur d'alternants » du score orange, alternance seulement (2026-11-27, @maxence)
**Contexte :** T51 : les 382 180 « recruteurs potentiels » de La bonne alternance (T11) sont des entreprises susceptibles d'embaucher des alternants **sans offre publiée** : exactement l'opportunité cachée.
**Décision :** `radar/recruteurs.py` marque `recruteur_lba` = l'entreprise est dans `data/raw/lba_recruteurs.parquet` avec au moins un code ROME **non ambigu** du domaine (`rome` de `domains.yaml`, pas `rome_partiel`) ; lecture DuckDB des seuls SIRET du rayon. Nouvelle composante **`c_recruteur_lba`** (0/1) du score pondéré (D22), curseur « Recruteur d'alternants (LBA) », **poids 2 par défaut**. Elle ne compte qu'en **alternance et « Tous »** : pour un autre contrat son poids est ignoré (`applicable_weights`), sinon elle vaudrait 0 partout et ferait baisser tous les scores sans rien classer ; même règle pour l'opportunité cachée, qui ne compte plus en « Tous » (elle y valait toujours 0). Une composante sans poids a un apport `NaN` : la liste et la fiche n'affichent que les composantes actives.
**Alternatives écartées :** un simple badge sans effet sur le classement (le signal mérite d'être pondérable) ; ajouter les recruteurs LBA absents du référentiel comme nouveaux points (souvent < 10 salariés, hors SIRENE T20, pas de score) ; utiliser aussi les codes `rome_partiel` (faux positifs : analyste financier, chef de projet informatique…).
**Conséquences :** France : 28 733 recruteurs LBA sur un ROME data, dont 12 378 dans le référentiel et 11 171 sans offre data (donc en orange). Rennes 20 km, alternance : 206 entreprises marquées sur 4 447. T28 (`c_embauche` réel, @emma) peut réutiliser `radar/recruteurs.py`.

---

### D25 — API ROMEO testée et non retenue pour classer les offres (2026-11-27, @emma)
**Contexte :** T14. Les offres Adzuna n'ont pas de code ROME, donc `classify` ne s'appuie que sur des mots-clés dans le titre. ROMEO (France Travail) prédit des codes ROME à partir d'un intitulé : on espérait un classement plus robuste et une T9 plus simple.
**Test :** 200 titres distincts tirés des vraies offres Adzuna : 50 titres anglais et 50 titres français classés `autre`, plus 20 titres classés par domaine. Code ROME n°1 de ROMEO → domaine via `domains.yaml` ; chaque désaccord avec les mots-clés a été relu à la main. Deuxième passe avec la description (500 car.) en `contexte`.
**Résultats :**
- titres `autre` que ROMEO place dans un domaine : 27/100, dont **~13 justes** (PMO, SOC Analyst, ServiceNow…) et ~12 faux (« Customer Success Manager » → vérification client bancaire, « Account Executive » → fusions-acquisitions, « Hardware Architect » → architecte base de données) ;
- titres déjà classés : accord 51/100 ; sur les désaccords, **les mots-clés ont raison ~26 fois, ROMEO ~10 fois** (ROMEO corrige quelques vraies erreurs : paie en cabinet comptable → rh, « CFO » courant faible, SEO + IA → marketing) ;
- le `scorePrediction` (0,60–0,85) ne sépare pas les bonnes réponses des mauvaises ;
- avec la description, le code change pour 147/200 titres, sans gain (accord 48/100).

**Décision :** ne pas brancher ROMEO dans `classify` ni dans le pipeline ; garder les mots-clés de `domains.yaml` (T6, T8).
**Alternatives écartées :** ROMEO seul (moins bon que les mots-clés) ; ROMEO en repli sur les `autre` au-dessus d'un seuil (gain de quelques dizaines de titres pour ~25 % d'erreurs, et un appel réseau de plus dans le pipeline).
**Conséquences :** pas de nouvelle dépendance ni de nouveau scope à ajouter dans les `.env`. T9 se fera avec des codes ROME et des mots-clés, comme T6. Si les besoins changent, les détails techniques de l'API (point d'accès, limites) sont dans `SOURCES.md`.

### D24 — Procédures collectives (BODACC) : pénaliser et alerter, sans supprimer (2026-11-27, @celia)
**Contexte :** T23. Recommander une entreprise en difficulté sans le dire décrédibilise l'outil ; mais la supprimer ferait perdre de l'information (à terme, Radar veut recenser un maximum d'entreprises avec leur situation).
**Décision :** collecte des annonces BODACC « procédures collectives » des **2 dernières années** (~405 000, un export parquet, cache `data/raw/bodacc_collectives.parquet`) ; pour chaque SIREN, le **dernier événement qui change la situation** : `sauvegarde`, `redressement`, `liquidation` (y compris clôture pour insuffisance d'actif et plan de cession), `plan` (plan adopté, l'entreprise poursuit) ou `fin` (procédure close sans liquidation → plus d'alerte). Colonnes `procedure_type/_date/_nature/_url` et `procedure_collective` dans `entreprises.parquet` ; **aucune entreprise supprimée**. Dans la couche orange (`radar/procedures.py`) : score multiplié par un coefficient qui dépend de la situation **et du contrat visé** (une alternance ou un emploi engage plus qu'un stage) — sauvegarde/plan ×0,85 (stage) à ×0,75 (alternance, emploi), redressement ×0,6 à ×0,4, liquidation ×0,1 à ×0,05 ; drapeau 🟡/🟠/🔴 + phrase + lien BODACC dans la liste et la fiche ; **liquidations masquées par défaut** (case « Afficher aussi les entreprises en liquidation », enregistrée dans le profil).
**Alternatives écartées :** supprimer les entreprises en difficulté (perte d'information ; une entreprise en sauvegarde ou sous plan continue de fonctionner) ; distinguer stages rémunérés et non rémunérés (l'app ne connaît pas la durée du stage, et un stage de plus de 2 mois est obligatoirement gratifié) ; toute l'histoire BODACC (un redressement de 2018 suivi d'un plan réussi ne doit plus pénaliser).
**Conséquences :** 11 124 établissements en alerte sur 406 266 (2,7 %) : 6 130 liquidations, 2 449 redressements, 2 046 plans, 499 sauvegardes. Coefficients réglables dans `PENALTIES` (`radar/procedures.py`). `build_all.py` réapplique BODACC après chaque extraction SIRENE (étape 1 bis). Pour actualiser : `uv run python scripts/collect_bodacc.py --refresh`.

### D23 — P(réponse) dans l'app : classement au choix, bandeau « simulé » permanent (2026-11-27, @maxence)
**Contexte :** T37 : brancher le démonstrateur T36 (D18) dans la couche orange sans laisser croire qu'il s'agit de vraies probabilités.
**Décision :** `radar/response/predict.py`. L'app lit `p_reponse.parquet` **pour les seuls SIRET affichés** (DuckDB) et ajoute la distance au logit : logit(p) = logit(p₀) + `coefficients['distance_10km']` × km / 10 (`modele_reponse.json`). Contrat visé : stage ou alternance → la ligne correspondante ; « Tous » → moyenne des deux ; « Emploi » → pas de P(réponse) (le modèle ne le couvre pas). Réglage « Classer les entreprises 🟠 par » : **Score** (défaut, explicable, D22) ou **P(réponse) simulée** (enregistré au profil, clé `tri`). Dès que P(réponse) est affichée : bandeau « 🧪 Démonstrateur — réponses simulées », colonne « P(réponse) simulée » en %, ligne « P(réponse) *simulée* » dans la fiche. Modèle absent, domaine non couvert ou emploi → message expliquant pourquoi, classement par score.
**Alternatives écartées :** P(réponse) comme 6ᵉ composante du score pondéré (mélangerait une grandeur simulée au score réel) ; tri par P(réponse) par défaut (le cœur du pitch reste le score explicable sur données réelles) ; charger tout `p_reponse.parquet` (France entière × 2 contrats).
**Conséquences :** l'app a besoin de `p_reponse.parquet` et `modele_reponse.json` (`scripts/build_response.py`, qui demande des scores construits **avec les offres Adzuna** : sur LBA seules, l'intensité est constante et la logistique échoue, matrice singulière).

---

### D22 — Score orange pondéré : moyenne des composantes, poids 0 à 5, apports affichés (2026-11-27, @maxence)
**Contexte :** T42 : l'étudiant règle les poids et le classement se recalcule en direct ; PROJET demande que chaque contribution soit affichée.
**Décision :** `score = Σ wⱼ·cⱼ / Σ wⱼ` (reste dans [0, 1]) sur 5 composantes : `c_intensite` et `c_embauche` (D13), **`c_proximite`** = 1 − distance / rayon, **`c_cachee`** = 1 si l'entreprise publie des offres du domaine mais aucune pour le contrat visé (l'« opportunité cachée » du pitch ; toujours 0 avec « Tous »), `c_dynamisme` (neutre tant que T22 manque). Curseurs entiers de 0 à 5, défaut intensité 3, besoin 3, proximité 1, opportunité cachée 1, dynamisme 0 ; bouton « Poids par défaut ». Chaque composante a une colonne `apport_<c>` = wⱼ·cⱼ / Σw, dont la somme est le score : affichée dans la liste (« + … ») et en barres dans la fiche de la carte. Tous les poids à 0 → repli sur le score D13. Poids enregistrés dans le profil (`poids_*`). Code : `radar/spontaneous.py` (`COMPONENTS`, `DEFAULT_WEIGHTS`, `weighted_score`).
**Alternatives écartées :** moyenne géométrique pondérée (exige toutes les composantes, mais apports non additifs, moins lisibles) ; poids en pourcentages devant totaliser 100 (curseurs liés, pénibles à régler).
**Conséquences :** l'opportunité cachée et la proximité ne sont plus que des réglages : une entreprise sans aucune offre peut passer devant une entreprise « cachée » si l'étudiant le veut. Le score n'est pas stocké (calculé dans l'app, cf. ARCHITECTURE).

---

### D21 — ⏸️ REPORTÉE — Noter les domaines autres que data (2026-11-27, @emma)
**Statut (2026-11-27) :** reportée. L'équipe se concentre **uniquement sur les offres data** pour le moment. La proposition ci-dessous reste valable si on rouvre le sujet. Il faudra alors d'abord compter, sur les vraies données LBA (T17), les offres et recruteurs par domaine. Ce qui nous concerne déjà pour data, via T51 et T28 : les recruteurs LBA et La Bonne Boîte sur les codes ROME data.
**Contexte :** depuis D20, l'app propose tous les domaines de `domains.yaml`, mais `scores.parquet` ne contient que data (`SCORED_DOMAINS = ("data",)`, D13). Si un étudiant choisit finance, marketing, rh ou informatique, **la couche 🟠 est vide** (`radar/spontaneous.py › load_nearby` filtre `s.domaine = ?`). Le calcul du score est pourtant générique. La vraie limite, c'est la donnée : toutes les offres Adzuna viennent de la recherche « data », donc pour un autre domaine on ne compterait que les offres qui mentionnent « data ».
**Proposition :**
1. **Source principale pour les autres domaines : La bonne alternance**, qui couvre **tous les métiers**, avec codes ROME, sur toute la France et sans quota : 12 748 offres et surtout 382 180 recruteurs potentiels (T11). Le nombre d'offres LBA du domaine (via `classify`, déjà dans `offres.parquet`) alimente l'intensité. Le fait qu'un recruteur LBA recrute un code ROME du domaine peut alimenter `c_embauche`, ce qui rejoint T24/T28.
2. **En complément, les offres Adzuna du domaine** (biaisées vers la data), avec dans l'app la mention « **signal partiel** » pour tout domaine autre que data.
3. Concrètement : `SCORED_DOMAINS` = toutes les clés de `domains.yaml` ; une colonne `signal` dans `scores.parquet` (`complet` pour data, `partiel` sinon), affichée par l'app.
**Alternatives écartées :** collecter Adzuna domaine par domaine (quota ~240 appels/jour partagé, déjà juste pour data) ; laisser la couche 🟠 vide hors data (l'app promet un domaine paramétrable).
**Conséquences si validée :** changement dans `radar/score/build.py` (@mathis, ou @emma avec son accord) et affichage du signal dans l'app (@maxence). Pour les slides, c'est une limite assumée et expliquée. Il faut les **vraies** données LBA (T17) pour vérifier les volumes par domaine avant de trancher.

### D20 — Filtres de l'app : domaines de `domains.yaml`, taille en 4 tranches, secteur = section NAF (2026-11-27, @maxence)
**Contexte :** T41 : filtrer par domaine, contrat, taille et secteur.
**Décision :** liste des domaines lue dans `radar/domains.yaml` (ajouter un domaine = l'ajouter au fichier, T9) ; les offres 🔵 sont classées dans l'app par le même classifieur que T13 (`radar.domains.classify`, ROME + titre), à la place du filtre « data » v0 par mots-clés ; le score 🟠 est celui du domaine choisi. Taille : 4 tranches lisibles (10–49, 50–249, 250–999, 1 000 et plus) regroupant les codes INSEE ; secteur : **section NAF** (21 lettres), prise dans `naf_section` ou déduite du code NAF. Choix multiples, liste vide = pas de filtre ; taille/secteur inconnus écartés dès qu'on filtre. Code : `radar/filters.py`. Réglages enregistrés dans le profil (`tailles`, `secteurs`).
**Alternatives écartées :** divisions NAF (88, liste trop longue dans une barre latérale) ; catégorie PME/ETI/GE (3 valeurs, presque tout est PME) ; lire `offres.parquet` dans l'app pour le domaine des offres (l'app lit encore les offres brutes).
**Conséquences :** taille et secteur ne filtrent que la couche 🟠 (L20). Les profils enregistrés avec l'ancien domaine « Data » retombent sur le domaine par défaut.

---

### D19 — Couche orange : « sans offre correspondante » = domaine × contrat visé, au niveau SIREN (2026-11-27, @maxence)
**Contexte :** T40 doit afficher les entreprises proches sans offre correspondante (D8), classées par score (D13), sur toute la France.
**Décision :** `radar/spontaneous.py`. Lecture DuckDB de `scores.parquet` ⋈ `entreprises.parquet` sur le **rectangle** du rayon (pas de chargement de la France entière), puis distance haversine ≤ rayon. Exclusion : offres du domaine **du contrat visé** (stage → `n_stage_domaine`, alternance → `n_alternance_domaine`, emploi → le reste, Tous → toutes), comptées au niveau **SIREN** quand le score réel les fournit (`*_siren`), sinon au niveau SIRET (données factices) ; `volume_suspect` écarté. Une entreprise qui recrute en emploi data mais sans stage reste donc orange pour un étudiant en stage : c'est l'opportunité cachée. Score v0 = √(`c_intensite` × `c_embauche`) (D13), en attendant les poids de T42. Géocodage : API Géoplateforme (BAN, sans clé) avec cache disque ; adresse introuvable ou réseau coupé → message, l'app continue. Carte : 300 meilleures entreprises au plus (la liste garde tout). La couche bleue est filtrée par le même rayon.
**Alternatives écartées :** charger tout `scores.parquet` en mémoire dans l'app (trop lourd France entière) ; exclusion par SIRET seulement (un établissement secondaire apparaîtrait orange alors que le siège publie l'offre).
**Conséquences :** l'app a besoin de `data/processed/{entreprises,scores}.parquet` (`scripts/build_all.py`) ; sans eux, la couche orange affiche un message. T42 remplacera `spontaneous_score` par une somme pondérée.

---

### D18 — Modèle de réponse : simulation sur entreprises réelles et logistique (2026-11-27, @mathis)
**Contexte :** mise en œuvre de D6. Aucune donnée ouverte ne dit qui répond aux candidatures spontanées ; il faut montrer que la chaîne fonctionne et l'expliquer à un jury de statisticiens.
**Décision :** T35 `radar/response/simulate.py` : 3 000 étudiants simulés dans 14 villes étudiantes, 15 candidatures chacun dans un rayon de 40 km, ciblant plutôt les entreprises bien notées (comme avec Radar). Réponse positive tirée selon une règle logistique documentée dans **`radar/response/params.yaml`** (c_intensite, c_embauche, log effectif, distance, alternance, offre visible) + **effet entreprise non observé** (σ = 0,5). T36 `radar/response/model.py` : logistique (statsmodels), test sur des étudiants jamais vus ; P(réponse) par (siret, contrat) **à distance nulle** + contributions ; l'app ajoute le terme de distance avec le coefficient de `modele_reponse.json`. Rapport régénéré automatiquement : `docs/MODELE_REPONSE.md`.
**Alternatives écartées :** réponses générées par un LLM (règle inconnue, rien à vérifier) ; un modèle à arbres (moins lisible, les paramètres ne se comparent pas à la règle) ; un GLMM avec effet entreprise (plus juste, mais l'intérêt pédagogique est justement de montrer l'atténuation).
**Conséquences :** AUC 0,646 (plafond 0,692 avec la vraie règle), calibration quasi parfaite, **7 paramètres sur 7 retrouvés** dans l'IC 95 % une fois l'atténuation (≈ 0,96, non-collapsibilité du logit) prise en compte. Toujours afficher « réponses simulées » (`donnees_simulees`). T37 (app) : trier la couche orange par P(réponse) ajustée de la distance.

### D17 — Titres anglais : mots-clés ajoutés d'après les vraies offres (2026-11-27, @emma)
**Contexte :** T8. Sur les 10 776 offres Adzuna réelles, 41,6 % étaient classées `autre`, dont ~940 titres en anglais (« Analytics Engineer », « Business Analyst », « Talent Acquisition »…).
**Décision :** ajout dans `radar/domains.yaml` de motifs anglais **complets** (marqués `# T8`), retenus un par un après avoir regardé **toutes** les bascules d'un domaine à l'autre, pas seulement les sorties de `autre`. Choix à connaître :
- « Business Analyst », « Product Manager », « Tech Lead », « Solution Architect », consultants SAP/ERP/Salesforce → **informatique** (ROME : consultant fonctionnel SI). Effet de bord assumé : 87 « Business Analyst Crédit/Assurance – Services financiers » passent de finance à informatique.
- `acquisition` seul (marketing) attrapait « Talent Acquisition » → remplacé par « paid/user acquisition », « acquisition manager »…, et `talent acquisition` exclu du marketing → **rh**.
- « GenAI » seul ne suffit pas pour data (« GenAI Sales Specialist ») : il faut « GenAI/AI/ML engineer » ou « generative AI ».
- Les métiers hors des 5 domaines restent `autre` : commerce (Account Executive, SDR), recherche clinique (CRA), « Project Manager » générique.
**Alternatives écartées :** les embeddings multilingues ou un LLM (dépendances lourdes, coût, pas reproductible) ; la catégorie Adzuna (`Unknown` pour 43 % des offres).
**Conséquences :** `autre` passe de 41,6 % à 36,6 % ; data passe de 3 128 à 3 209 offres, informatique de 1 972 à 2 533. Il faut relancer `scripts/build_all.py` pour que `offres.parquet` et les scores en tiennent compte.

### D16 — Sécurité des mots de passe : règles CNIL simplifiées et blocage par compte (2026-11-27, @celia)
**Contexte :** T48 acceptait tout mot de passe de 8 caractères (`12345678` passait) et ne bloquait qu'à l'échelle d'un onglet (recharger la page suffisait à réessayer).
**Décision :** à la création, au moins **12 caractères et 3 types** parmi minuscules, majuscules, chiffres, caractères spéciaux (version simplifiée de la recommandation CNIL de 2022, qui laisse passer les phrases de passe) ; **liste noire** de mots de passe très répandus ; identifiant interdit dans le mot de passe ; message qui liste les règles non respectées. À la connexion, **blocage par compte enregistré en base** : 5 échecs d'affilée → 15 min de blocage, même avec le bon mot de passe. Les bases existantes sont mises à jour automatiquement (colonnes `failed_logins`, `locked_until`). Détails et manques : `docs/SECURITE.md`.
**Alternatives écartées :** règles NIST pures (longueur seule, sans types : moins lisible pour un jury français que la référence CNIL) ; vérification *Have I Been Pwned* (appel réseau externe, envoi d'un préfixe d'empreinte) ; blocage par adresse IP (derrière le proxy Onyxia, tous les utilisateurs ont la même).
**Conséquences :** les comptes de test créés avant D16 gardent leur ancien mot de passe (seule la création est contrôlée). Le message de blocage révèle qu'un identifiant existe (L19), accepté pour la démo.

---

### D15 — Pipeline en une commande et rattrapage local du rapprochement (2026-11-27, @mathis)
**Contexte :** T50 (enchaîner les étapes sans erreur d'ordre) et T25 (L6 : des entreprises comme SFR apparaissaient « sans offre », donc à tort dans la couche orange).
**Décision :** `scripts/build_all.py` enchaîne SIRENE (si absent) → `classify_offres` (T13) → `match_offres` (T21) → `build_scores` (T30) et vérifie chaque fichier contre son schéma ; la collecte reste à part (quotas). Rattrapage **local** dans `match_siret.py` : candidats en **cascade** (si un candidat est refusé, on essaie le suivant : « Atos » → PME homonyme lointaine refusée → ATOS FRANCE), noms sans espaces, **morceaux du nom légal** (« … - S.F.R »), **enseignes**, sigles à points recollés avant normalisation, préférence ETI/GE entre homonymes ; `alias`/`enseigne` refusés au-delà de 50 km (≈ 1 sur 2 juste), préfixe lointain refusé pour les noms de 3 lettres.
**Alternatives écartées :** l'API Recherche d'entreprises pour les noms restants : ils correspondent surtout à des entreprises hors référentiel (< 10 salariés ou effectif inconnu), donc sans effet sur la couche orange ni sur le score, pour une dépendance réseau en plus.
**Conséquences :** 65,1 % des offres d'employeurs rapprochées (63,4 % avant), 523 entreprises avec au moins une offre data (503 avant). Reste une erreur connue (Groupe Casino → Casino de Paris).

### D14 — Comptes facultatifs : démo anonyme par défaut, connexion pour garder profil et historique (2026-11-27, @celia)
**Contexte :** l'équipe veut pouvoir se connecter pour retrouver son profil et ses recherches, sans casser la contrainte de `PROJET.md` : l'appli marche en démo **sans données saisies par les utilisateurs**.
**Décision :** deux modes. **Anonyme** (par défaut) : aucune écriture, tout reste dans `st.session_state`. **Connecté** (facultatif) : comptes et profils dans une base SQLite `data/app/radar.db` (hors Git). Mots de passe hachés avec **scrypt** (bibliothèque standard, sel par compte, comparaison à temps constant). Code serveur dans `radar/accounts.py` (testable sans Streamlit), bloc de la barre latérale dans `app/compte.py`. Le **profil = les valeurs des widgets de recherche** listés dans `PROFILE_KEYS` (`app/streamlit_app.py`) : chaque widget porte une `key`, le profil est rechargé dans `st.session_state` à la connexion, et les valeurs devenues invalides (région disparue…) sont ignorées. Historique (T49) : table `recherches` ; Streamlit relançant la page à chaque réglage, les changements faits à moins de 2 min de la dernière recherche la mettent à jour (on garde l'état final), une recherche identique n'est pas dupliquée, 50 recherches max par compte.
**Alternatives écartées :** `streamlit-authenticator` (proposé d'abord : interface qui change d'une version à l'autre, comptes attendus dans un YAML) ; `st.login` (OIDC Google/GitHub : application OAuth et URL de retour à gérer sur Onyxia, trop long en 24 h) ; connexion obligatoire (la démo doit marcher en un clic).
**Conséquences :** ajouter un réglage à l'app (T40, T41, T42) = lui donner une `key` et l'ajouter à `PROFILE_KEYS`, sinon il n'est pas enregistré. Les valeurs par défaut de ces widgets se posent avec `st.session_state.setdefault(...)`, pas avec `value=` (sinon Streamlit avertit quand un profil les remplace). L'adresse est une donnée personnelle : « Supprimer mon compte » efface tout. Limites (base locale à chaque service Onyxia, perdue s'il est supprimé ; déconnexion au rechargement) dans `LIMITES.md` (L17, L18). Pour le pitch : l'historique prépare le vrai modèle de réponse (D6).

### D13 — Score v0 : gamma-Poisson par division NAF, exposition pondérée par la couverture (2026-11-27, @mathis)
**Contexte :** l'a priori bêta-binomial prévu (part des offres de l'entreprise qui sont data) suppose de connaître **toutes** les offres de l'entreprise. Or la collecte Adzuna ne porte que sur la requête « data », et seules 6 régions sur 13 sont collectées (Île-de-France à 35 %).
**Décision :** `radar/score/` — k_i ~ Poisson(λ_i · E_i), λ_i ~ Gamma(α_s, β_s), avec λ en **offres data pour 100 salariés** et E_i = Σ effectif × couverture de la région / 100. A priori estimé par la méthode des moments de **Clayton & Kaldor**, par **division NAF** (2 chiffres) lissée vers sa section, elle-même lissée vers la moyenne globale. Au niveau SIREN (le besoin est celui de l'entreprise), hérité par ses établissements. Composantes : `c_intensite` = rang de λ a posteriori ; `c_embauche` = rang du besoin attendu **de l'établissement** (λ × effectif local) — proxy en attendant La Bonne Boîte / recruteurs LBA (`c_embauche_source`) ; `c_dynamisme` = 0,5 neutre tant que T22 n'est pas faite (`c_dynamisme_disponible`). Intérim (NAF 78) non noté ; `volume_suspect` si plus d'offres data que la moitié de l'effectif. Seul le domaine **data** est noté (les autres domaines ne sont vus qu'à travers la requête « data »).
**Alternatives écartées :** bêta-binomial (dénominateur inconnu) ; a priori par section (le cinéma recevait l'a priori de la programmation) ; besoin attendu au niveau de l'entreprise (chaque bureau de La Poste héritait de 250 000 salariés).
**Conséquences :** une entreprise hors zone collectée reçoit exactement l'a priori de son secteur (affiché via `couverture = 0`). Classement conseillé pour la couche orange : entreprises avec `n_offres_domaine_siren == 0`, `volume_suspect == False`, triées par la moyenne géométrique de `c_intensite` et `c_embauche` (exemple en Ille-et-Vilaine : France Télévisions, Hellowork, Tessi, Claranet, Klaxoon, Ouest-France). Limite : les entreprises non rapprochées en T21 (ex. SFR) apparaissent « sans offre ». Validation : l'estimateur retrouve les vrais paramètres sur données simulées (`tests/test_intensity.py`).

### D12 — Référentiel SIRENE : fusion des deux versions de T20 (2026-11-27, @celia)
**Contexte :** T20 a été réalisée deux fois en parallèle (@celia, puis @mathis, car le push de Celia était bloqué). Les deux versions lisaient les mêmes stocks SIRENE à distance avec DuckDB, avec le même filtre (actif, ≥ 10 salariés, `'NN'` exclu, NAF rév. 2) et donnaient 406 266 établissements.
**Décision :** la base est la version de Mathis : T21 utilise déjà `effectif_estime` et le `nom` de l'unité légale, et `scripts/extract_sirene.py` appelle `extract()` / `save()`. Ajouts repris de la version de Celia : prénom + nom pour les entrepreneurs individuels sans dénomination, colonnes `tranche_libelle` et `adresse` (vide si diffusion partielle, comme lat/lon), option `--dep` pour tester sur un département, tests sur les tranches et la requête.
**Alternatives écartées :** garder les deux modules (doublon) ; la table NAF en CSV versionné de Celia (le parquet NAF de data.gouv donne aussi section et division) ; `procedure_collective = False` par défaut (NA est plus juste tant que T23 n'est pas faite).
**Conséquences :** un seul point d'entrée, `uv run python scripts/extract_sirene.py [--dep 35]`. `radar/naf_rev2.csv` et son exception dans `.gitignore` sont supprimés.

### D11 — Rapprochement offres → SIRET : règles et intermédiaires (2026-11-27, @mathis)
**Contexte :** Adzuna ne donne que le nom affiché de l'entreprise. Il faut un SIRET pour compter les offres par entreprise (score) et pour exclure de la couche orange les entreprises qui ont déjà une offre (D8). 17 % des offres viennent de plateformes, de sites d'emploi ou de cabinets (Collective.work, Free-Work, Michael Page, intérim).
**Décision :** `radar/process/match_siret.py`, appelé par `scripts/match_offres.py` sur les lignes `a_rapprocher` seulement (D10). Ordre : intermédiaire (liste + motifs + NAF 78.*) → **pas de SIRET, voulu** ; puis `exact`, `sigle` (grandes entreprises seulement), `prefixe`, `flou` (seuil 94). On garde l'établissement le plus proche de l'offre. Au-delà de 50 km (`_loin`), on n'accepte que les noms distinctifs ou les ETI/GE ; `flou` lointain est refusé. Colonnes ajoutées : `siren_match`, `match_confiance` (haute / moyenne), `match_distance_km`, `intermediaire` — déclarées dans le schéma `offres_rapprochees` (D7).
**Alternatives écartées :** rapprocher aussi les intermédiaires (ils deviendraient les entreprises « les plus data ») ; un rapprochement flou sans contrainte de distance (≈ 0/10 juste sur échantillon).
**Conséquences :** 63 % des offres d'employeurs rapprochées (50 % en confiance haute). Le score peut se limiter à `match_confiance == "haute"`. L'app et le score filtrent `intermediaire == False`. La liste des intermédiaires est à compléter quand de nouvelles sources arrivent.

### D10 — offres.parquet : T13 classe, T21 rapproche (2026-11-27, @emma)
**Contexte :** `offres.parquet` reçoit des colonnes de deux tâches menées en parallèle : `domaine`/`contrat` (T13, @emma) et `siret_match`/`match_score`/`match_methode` (T21, @mathis). Il ne faut pas que l'une écrase le travail de l'autre.
**Décision :** T13 (`radar/process/classify.py`) écrit `offres.parquet` à partir de toutes les offres brutes. Il remplit le SIRET seulement quand la source le donne (`siret_source`), retire celui des offres déléguées à une école (`siret_ecole_exclu`) et marque les autres `a_rapprocher`. T21 relit `offres.parquet` et ne complète que les lignes `a_rapprocher`, avec sa propre valeur de `match_methode`. Chaque classement garde la règle qui l'a décidé (`domaine_regle`, `contrat_regle`) pour pouvoir l'expliquer. Pour le contrat, le titre l'emporte sur le `contract_type` d'Adzuna (rarement rempli, et seulement permanent/contract).
**Alternatives écartées :** que T21 écrive son propre fichier (deux versions des offres à réconcilier dans T50) ; que T13 attende T21 (on perdrait du temps sur le chemin de la V1).
**Conséquences :** ordre du pipeline (T50) : collecteurs → `classify_offres.py` → rapprochement T21 → score. `quick_filter.py` (T39) peut être remplacé par `offres.parquet` dans l'app (à voir avec Maxence).

### D9 — Dictionnaire des domaines : codes ROME sûrs, codes ambigus et mots-clés (2026-11-27, @emma)
**Contexte :** classer chaque offre par domaine (T6 → T13). La bonne alternance fournit des codes ROME, mais pas Adzuna (titre seulement). Certains codes ROME sont ambigus (« Chargé d'études commerciales » peut être un poste data ou marketing).
**Décision :** `radar/domains.yaml` décrit 5 domaines, dans l'ordre data, informatique, finance, marketing, rh (l'ordre départage les cas ambigus : data gagne). Pour chacun :
- `rome` : les codes sûrs, chacun dans un seul domaine ;
- `rome_partiel` : les codes ambigus, qui ne comptent que si le titre contient un mot-clé du domaine ;
- `mots_cles` et `exclusions` : des expressions régulières sur le titre.

Règle (`radar/domains.py › classify`) : code ambigu confirmé par le titre, sinon code sûr, sinon titre seul, sinon `autre`. Les codes ont été vérifiés avec l'API ROME 4.0 (1 923 métiers) et leurs libellés recopiés. Les mots-clés data reprennent ceux de `quick_filter.py` (T39) : les verdicts sont identiques sur ses titres de test.
**Alternatives écartées :** des mots-clés seuls (on perdrait le ROME, fiable quand il existe) ; des codes seuls (inutilisables pour Adzuna).
**Conséquences :** T13 s'appuie sur `classify` et peut y ajouter la description. Ajouter un domaine = ajouter un bloc dans le YAML, sans toucher au code (mais `fake_data.DOMAINS` doit suivre : un test le vérifie). Les titres en anglais hors data sont mal couverts (« Accounting Generalist » → `autre`).

### D8 — Carte à deux couches : offres réelles / candidature spontanée (2026-11-27, @mathis)
**Contexte :** l'équipe veut que la démo repose sur une carte montrant à la fois les vraies offres et les entreprises susceptibles d'accepter une candidature spontanée.
**Décision :** une carte folium, deux couches activables. 🔵 Offres réelles (filtrées domaine × contrat visé, lien vers l'annonce). 🟠 Candidature spontanée : entreprises **sans offre correspondante**, classées par score ou P(réponse). Les deux couches sont exclusives (une entreprise avec une offre correspondante est en bleu).
**Conséquences :** l'appli a besoin de `offres.parquet` (avec SIRET quand il est connu, pour l'exclusion) et de `scores.parquet` / `p_reponse.parquet`. La couche 1 peut être faite dès maintenant (T39).

### D7 — Contrat de données vérifiable en code + données factices (2026-11-27, @emma)
**Contexte :** T5 doit produire des données qui respectent les schémas de `ARCHITECTURE.md`, et chaque module doit pouvoir vérifier qu'il les respecte aussi.
**Décision :** `radar/schemas.py` recopie en code les colonnes minimales du tableau de `ARCHITECTURE.md`, avec `check_columns(df, nom)` (les colonnes en plus sont permises). Les offres brutes vont dans `data/raw/offres_raw/<source>.parquet`, comme le prévoit T12. Le générateur factice (`radar/fake_data.py`) est reproductible (graine fixe) et ne décrit que des entreprises inventées : SIRET aléatoires mais valides (clé de Luhn), URL en `example.org`, descriptions marquées `[DONNÉE FACTICE]`.
**Alternatives écartées :** un générateur sans vérification de schéma (les écarts n'apparaîtraient qu'au branchement des vraies données, à H+8).
**Conséquences :** si on change un schéma, il faut mettre à jour **le tableau et `schemas.py`**. Les fichiers `scores`, `candidatures_simulees` et `p_reponse` factices ont les bonnes colonnes, mais leurs formules sont provisoires : T30/T31 et T35/T36 les remplaceront.

### D6 — Modèle de réponse entraîné sur des réponses simulées (2026-11-27, @mathis)
**Contexte :** l'équipe veut un modèle « qui va répondre à une candidature spontanée », mais aucune donnée ouverte ne contient ces réponses. Le but pour le hackathon : montrer que la chaîne fonctionne.
**Décision :** les entreprises et leurs variables sont réelles ; seule la réponse est simulée, selon une règle paramétrique (paramètres documentés dans `radar/response/params.yaml`). On entraîne un modèle et on montre la calibration, l'AUC et les paramètres retrouvés.
**Alternatives écartées :** générer les réponses avec un LLM (non reproductible, payant, règle inconnue donc on ne peut pas vérifier que le modèle la retrouve).
**Conséquences :** **toujours étiqueter comme simulé** (app + slides). Réponse préparée pour le jury : la chaîne sera réentraînée sur de vrais retours d'utilisateurs.

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
