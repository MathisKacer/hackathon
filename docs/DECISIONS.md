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

### D14 — Comptes facultatifs : démo anonyme par défaut, connexion pour garder profil et historique (2026-11-27, @celia) — *proposition, à valider par l'équipe*
**Contexte :** l'équipe veut pouvoir se connecter pour retrouver son profil et ses recherches, sans casser la contrainte de `PROJET.md` : l'appli marche en démo **sans données saisies par les utilisateurs**.
**Décision :** deux modes. **Anonyme** (par défaut) : aucune écriture, tout reste dans `st.session_state` et disparaît en fermant l'onglet. **Connecté** (facultatif) : `streamlit-authenticator` (mots de passe hachés bcrypt, cookie de session signé par une clé du `.env`), et une base SQLite `data/app/radar.db` avec 3 tables : `users`, `profils` (domaine, contrat, adresse, rayon, filtres, poids), `recherches` (date, paramètres en JSON, nombre de résultats, top 5 SIRET). Code isolé dans `radar/accounts.py` ; l'app ne fait qu'appeler `load_profile` / `save_profile` / `log_search`.
**Alternatives écartées :** `st.login` (OIDC Google/GitHub : il faut créer une application OAuth et gérer des URL de retour sur Onyxia, trop long en 24 h) ; un fichier YAML de comptes versionné (des mots de passe, même hachés, n'ont rien à faire dans Git) ; rendre la connexion obligatoire (la démo doit marcher en un clic).
**Conséquences :** l'adresse saisie est une donnée personnelle : on stocke le minimum, et « Supprimer mon compte » efface tout. Le pod Onyxia est éphémère : la base est perdue au redémarrage, ce qui est acceptable pour la démo (à présenter comme une perspective : base hébergée). Pour le pitch, l'historique prépare le terrain du vrai modèle de réponse (D6) : avec un suivi des candidatures, on aurait de vraies réponses à la place des simulées.

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
