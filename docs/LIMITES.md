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
| L6 | **37 % des offres d'employeurs non rapprochées** (sigles absents de SIRENE : SFR, EY ; noms commerciaux ≠ noms légaux : Pennylane…) | Ces entreprises apparaissent « sans offre » → **peuvent sortir à tort dans la couche orange** (ex. SFR, 38 offres) | ✅ rattrapage par l'API Recherche d'entreprises (recherche plein texte, gère sigles et noms commerciaux) + table d'alias pour les plus gros émetteurs | **T25** | « 63 % de rapprochement, taux affiché » |
| L7 | Groupes : les offres sont rattachées à **une** entité juridique (Sanofi → une petite société de 14 salariés) ; les autres sociétés du groupe paraissent sans offre | Mêmes faux positifs orange pour les filiales ; quelques `volume_suspect` | ✅ en partie : regrouper par « famille de marque » (même début de nom, ETI/GE) pour l'exclusion | **T26** | — |
| L8 | Intermédiaires non repérés (liste manuelle + motifs + NAF 78) | Un cabinet peut passer pour un employeur très « data » (Orel Services : 37 offres / 14 salariés → `volume_suspect`) | ✅ revue des plus gros émetteurs à chaque nouvelle source | **T27** | — |
| L9 | Homonymes résiduels (« MSF International » → « M&S International ») | Quelques rapprochements faux, surtout `flou` et `_loin` | ✅ partiel : n'utiliser que `match_confiance == "haute"` dans le score si besoin | T25 | — |

## Score (T30, D13)

| # | Limite | Impact | Réglable ? | Tâche | À dire au pitch |
|---|---|---|---|---|---|
| L10 | `c_dynamisme` neutre (0,5) : finances non chargées | Le dynamisme ne joue pas dans le classement | ✅ ratios financiers INPI en masse (data.economie.gouv.fr) plutôt que 276 000 appels d'API | T22 | — |
| L11 | `c_embauche` = proxy (intensité × effectif local), pas une vraie probabilité d'embauche | Favorise les gros établissements des secteurs data | ✅ La Bonne Boîte v2 (codes ROME data × départements, ≤ 1 req/s) et recruteurs potentiels La bonne alternance | **T28** | — |
| L12 | Intensité calculée au niveau de l'entreprise (SIREN) et héritée par tous ses établissements | Un site de production d'un groupe très data hérite de son intensité | ⚠️ partiel : pondérer par la division NAF de l'établissement | T28 | — |
| L13 | Divisions NAF sans offres (ex. 59 « cinéma ») : a priori proche de celui de leur section | Quelques secteurs légèrement surévalués | ✅ hiérarchie à 3 niveaux (classe NAF) ou a priori par division seulement si assez d'entreprises | (faible priorité) | — |
| L14 | Effectifs SIRENE = tranches, millésime 2024 | Exposition approximative (moyenne géométrique de la tranche) | ❌ | — | — |
| L15 | **Pas de vérité terrain** : on ne sait pas qui répond aux candidatures spontanées | Le modèle de réponse est un **démonstrateur sur réponses simulées** (D6) | ⏳ retours des utilisateurs après lancement | T35–T37, T34 | « Entreprises réelles, réponses simulées ; chaîne prête à être réentraînée » |

## Données personnelles

| # | Limite | Impact | Réglable ? | Tâche |
|---|---|---|---|---|
| L16 | SIRENE contient des noms de personnes physiques (dirigeants, entrepreneurs individuels) | Ne pas les afficher comme « contacts » ; positions masquées si diffusion partielle (fait) | ✅ règle d'affichage dans l'app | T43 |

## Comptes (T48)

| # | Limite | Impact | Réglable ? | Tâche | À dire au pitch |
|---|---|---|---|---|---|
| L17 | Base des comptes en SQLite **dans le pod Onyxia** | Comptes et profils perdus au redémarrage du service ; un seul serveur | ✅ base hébergée (PostgreSQL) ou copie sur S3 | — | « Comptes en local pour la démo ; en production, une base hébergée » |
| L18 | Pas de « se souvenir de moi » ni de mot de passe oublié | Recharger la page (F5) déconnecte ; un mot de passe oublié = nouveau compte (pas d'e-mail collecté, volontairement) | ✅ cookie signé ; récupération par e-mail | — | « On ne collecte pas d'e-mail : minimum de données personnelles » |
