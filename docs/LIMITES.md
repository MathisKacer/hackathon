# Limites connues

> Ce que Radar ne sait pas (encore) faire, pourquoi, et si c'est réglable. Sert à deux choses :
> **assumer les limites au pitch** (colonne « À dire ») et **savoir quoi améliorer ensuite**
> (colonne « Tâche »). Mettre à jour dès qu'une limite est levée ou découverte.
> État au 2026-11-27, 14 h (après T20, T21, T30).

## Données d'offres

| # | Limite | Impact | Réglable ? | Tâche | À dire au pitch |
|---|---|---|---|---|---|
| L1 | Collecte Adzuna sur la seule requête « data » | Seul le domaine **data** est noté ; les autres domaines ne sont vus qu'à travers des offres qui contiennent « data » | ✅ en partie : collecter d'autres requêtes avec le quota des jours suivants ; les offres La bonne alternance (avec code ROME) couvrent tous les domaines pour l'alternance | T18, T17 | « Démo sur la data ; le modèle est générique, il suffit de collecter » |
| L2 | 6 régions sur 13 collectées, Île-de-France à 35 % (plafond de 100 pages), Nouvelle-Aquitaine partielle | Hors zone : score = moyenne du secteur (`couverture = 0`) | ✅ quota Adzuna de ~240 appels/jour → relancer chaque jour ; découper l'IDF par département | T16 | « Couverture affichée ; hors zone, estimation par secteur » |
| L3 | Instantané : offres de moins de 60 jours, collectées une fois | Le score décrit le marché **aujourd'hui** ; une entreprise qui recrute par à-coups peut être à 0 | ⏳ seulement avec le temps (collecte régulière) | — | « Avec quelques mois de collecte, on mesurerait la dynamique » |
| L4 | Les stages se publient surtout sur des plateformes sans API (JobTeaser, WTTJ, LinkedIn) | « Pas d'offre de stage » = pas d'offre **visible sur les canaux ouverts** | ❌ (CGU) | — | Formulation à garder telle quelle |
| L5 | Descriptions Adzuna tronquées (~500 caractères), offres placées au centre de la commune | Classification surtout sur le titre ; positions approximatives | ❌ côté Adzuna ; ✅ partiel avec les ATS (T15) | T15 | — |

## Rapprochement offres → entreprises (T21)

| # | Limite | Impact | Réglable ? | Tâche | À dire au pitch |
|---|---|---|---|---|---|
| L6 | **35 % des offres d'employeurs non rapprochées** (après T25). Restent surtout des entreprises **absentes du référentiel** : moins de 10 salariés, ou établissements sans effectif connu dans SIRENE (Pennylane, Segula, Crédit Agricole CIB) | Peu d'effet sur la couche orange (une entreprise absente du référentiel n'y apparaît pas) ; ces offres ne comptent pas dans l'intensité | ⚠️ ajouter au référentiel les établissements à effectif inconnu des ETI/GE ; l'API Recherche d'entreprises retrouverait le SIREN mais pas d'établissement noté → écartée | T25 ✅ (SFR, Atos, LCL, GMF, Geodis retrouvés) | « 65 % de rapprochement, taux affiché » |
| L7 | Groupes : les offres sont rattachées à **une** entité juridique (Sanofi → une petite société de 14 salariés) ; les autres sociétés du groupe paraissent sans offre | Mêmes faux positifs orange pour les filiales ; quelques `volume_suspect` | ✅ en partie : regrouper par « famille de marque » (même début de nom, ETI/GE) pour l'exclusion | **T26** | — |
| L8 | Intermédiaires non repérés (liste manuelle + motifs + NAF 78) | Un cabinet peut passer pour un employeur très « data » (Orel Services : 37 offres / 14 salariés → `volume_suspect`) | ✅ revue des plus gros émetteurs à chaque nouvelle source | **T27** ✅ (revue faite après l'arrivée de LBA : organismes de formation, intérim/placement via SIRET source ; à refaire à chaque nouvelle source) | — |
| L9 | Homonymes résiduels (« MSF International » → « M&S International ») | Quelques rapprochements faux, surtout `flou` et `_loin` | ✅ partiel : n'utiliser que `match_confiance == "haute"` dans le score si besoin | T25 | — |

## Score (T30, D13)

| # | Limite | Impact | Réglable ? | Tâche | À dire au pitch |
|---|---|---|---|---|---|
| L10 | `c_dynamisme` neutre (0,5) : finances non chargées | Le dynamisme ne joue pas dans le classement | ✅ ratios financiers INPI en masse (data.economie.gouv.fr) plutôt que 276 000 appels d'API | T22 | — |
| L11 | `c_embauche` = proxy (intensité × effectif local), pas une vraie probabilité d'embauche | Favorise les gros établissements des secteurs data | ✅ **T28 (D27)** : les établissements signalés par La Bonne Boîte pour un métier data passent devant, classés par `hiring_potential` ; proxy pour les autres. Recruteurs LBA déjà comptés à part (`c_recruteur_lba`, D26) | **T28** | 🟡 partiellement levée : La Bonne Boîte ne couvre que **1 736 établissements data** en France (1 331 dans le référentiel, 0,3 %) ; les autres restent au proxy |
| L12 | Intensité calculée au niveau de l'entreprise (SIREN) et héritée par tous ses établissements | Un site de production d'un groupe très data hérite de son intensité | ⚠️ partiel : pondérer par la division NAF de l'établissement | T28 | — |
| L13 | Divisions NAF sans offres (ex. 59 « cinéma ») : a priori proche de celui de leur section | Quelques secteurs légèrement surévalués | ✅ hiérarchie à 3 niveaux (classe NAF) ou a priori par division seulement si assez d'entreprises | (faible priorité) | — |
| L14 | Effectifs SIRENE = tranches, millésime 2024 | Exposition approximative (moyenne géométrique de la tranche) | ❌ | — | — |
| L15 | **Pas de vérité terrain** : on ne sait pas qui répond aux candidatures spontanées | Le modèle de réponse est un **démonstrateur sur réponses simulées** (D6) : ses probabilités reflètent les hypothèses de `params.yaml`, pas le réel | ⏳ retours des utilisateurs après lancement (historique des recherches D14 + bouton « on m'a répondu ») | T35–T36 ✅, T37 ✅ (bandeau « simulé » dans l'app, D23), T34 | « Entreprises réelles, réponses simulées ; le modèle retrouve la règle cachée (7/7 paramètres, bien calibré) : il est prêt à apprendre des vrais retours » |
| L20 | Filtres **taille** et **secteur** (T41) appliqués aux entreprises 🟠 seulement | Les offres 🔵 n'ont pas d'effectif ni de NAF fiables (Adzuna n'en donne pas ; rapprochement SIRET à 65 %) : elles ne suivent que domaine, contrat, région, âge et mot-clé | ✅ filtrer les offres rapprochées d'un SIRET (`offres.parquet`) | — | « Les filtres taille/secteur servent à cibler les candidatures spontanées » |

## Situation des entreprises (BODACC, T23)

| # | Limite | Impact | Réglable ? | Tâche | À dire au pitch |
|---|---|---|---|---|---|
| L21 | Fenêtre de **2 ans** et instantané : une procédure ouverte avant, ou publiée après la collecte, n'est pas vue | Quelques entreprises en difficulté sans alerte | ✅ relancer `collect_bodacc.py --refresh` ; élargir `PERIOD_YEARS` | — | « Données BODACC du jour, procédures des 2 dernières années » |
| L22 | Annonces sans SIREN (entrepreneurs inscrits au seul répertoire des métiers) ignorées ; rattachement par SIREN, donc **tous les établissements** d'une entreprise sont signalés | Peu d'impact (≥ 10 salariés : surtout des sociétés au RCS) ; un établissement sain d'un groupe en procédure est pénalisé | ✅ en partie (rattacher par n° RM) | — | — |
| L23 | Coefficients de pénalité **fixés à dire d'expert** (pas estimés) | Classement sensible à ces choix | ✅ réglables dans `radar/procedures.py` ; à terme, estimés sur de vraies réponses | — | « Pénalité explicite et réglable, selon le contrat visé » |

## Entreprises et sites (T57)

| # | Limite | Impact | Réglable ? | Tâche | À dire au pitch |
|---|---|---|---|---|---|
| L24 | « Entreprise » = un **SIREN** (une société). Les **filiales d'un groupe** (Orange SA, Orange Business Services, Orange Cyberdéfense…) sont des entreprises distinctes, non reliées : le lien groupe → filiales n'existe pas en données ouvertes. Seuls les sites d'au moins 10 salariés sont listés | Une recherche « orange » montre plusieurs entreprises ; la fiche d'Orange SA ne liste pas les sites des filiales | ✅ en partie : rapprocher par le nom (familles de marque) | T26 | « Une entreprise = un SIREN ; les groupes viendront avec les familles de marque » |

## Données personnelles

| # | Limite | Impact | Réglable ? | Tâche |
|---|---|---|---|---|
| L16 | SIRENE contient des noms de personnes physiques (dirigeants, entrepreneurs individuels) | Ne pas les afficher comme « contacts » ; positions masquées si diffusion partielle (fait) | ✅ règle d'affichage dans l'app | T43 |

## Comptes (T48)

| # | Limite | Impact | Réglable ? | Tâche | À dire au pitch |
|---|---|---|---|---|---|
| L17 | Base des comptes = **un fichier SQLite** (`data/app/radar.db`) sur le disque persistant du service VS Code Onyxia | Conservée quand on relance l'app ou qu'on met le service en pause ; **perdue si le service est supprimé** ; **une base par membre de l'équipe** (un compte créé chez l'un n'existe pas chez l'autre) ; pas de sauvegarde | ✅ base hébergée (Supabase, T52) ou copie sur S3 | T52 | « Comptes en local pour la démo ; en production, une base hébergée » |
| L18 | Pas de « se souvenir de moi » ni de mot de passe oublié | Recharger la page (F5) déconnecte ; un mot de passe oublié = nouveau compte (pas d'e-mail collecté, volontairement) | ✅ cookie signé ; récupération par e-mail | — | « On ne collecte pas d'e-mail : minimum de données personnelles » |
| L19 | Sécurité des comptes au niveau « démo » : le blocage révèle qu'un identifiant existe ; pas de vérification contre les mots de passe fuités ni de double authentification | Faible pour la démo (pas de données sensibles, pas d'e-mail) | ✅ voir `docs/SECURITE.md` › Ce qui manque | — | « Règles CNIL, hachage scrypt, blocage après 5 échecs ; en production : 2FA et vérification des fuites » |
