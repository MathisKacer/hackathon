# Sources de données — inventaire

> État vérifié le 2026-11-27. ✅ = testé par un appel réel · 📄 = documentation seulement · ⚠️ = point bloquant ou risque.
> Mettre à jour la colonne « Statut » dès que quelqu'un obtient une clé ou teste une source.

## 🚨 Point bloquant : API Offres d'emploi France Travail

**L'API Offres d'emploi n'est plus exposée sur francetravail.io** : France Travail revoit ses conditions de diffusion après des usages massifs par des outils d'IA. L'accès se demande via le formulaire de contact de francetravail.io, sans garantie de délai. **On ne doit pas bâtir la démo dessus.** On fait la demande quand même et, si l'accès arrive, c'est un bonus.
Sources : [data.gouv – API Offres d'emploi](https://www.data.gouv.fr/dataservices/api-offres-demploi), [GovAPI Atlas – France Travail](https://govapiatlas.com/fr/org/france-travail/).

## 1. Offres d'emploi (signal « besoin data »)

| Source | Accès | Ce que ça apporte à Radar | SIRET ? | Fiabilité / limites | Statut |
|---|---|---|---|---|---|
| **Adzuna API** (`/jobs/fr/search`, `/top_companies`, `/histogram`) | Clé gratuite (app_id + app_key), inscription immédiate. Quota gratuit annoncé ~25/min, 250/jour, 2 500/mois (source tierce, à confirmer) | Offres actives agrégées (France). `top_companies` = nombre d'offres par entreprise pour une requête et un lieu → **intensité data directement**. Champs : titre, description **tronquée**, `company.display_name`, lieu + lat/lon, catégorie, salaire (souvent prédit), `contract_type`, `created`, `redirect_url` | ❌ nom seulement | Bonne couverture cadres/tech. Quota serré → collecte ciblée (Bretagne) + cache | 📄 → **clé à créer** |
| **API La bonne alternance** (api.apprentissage.beta.gouv.fr) | Gratuit, compte + jeton | Offres d'alternance (dont partenaires) **rattachées au SIRET** + « recruteurs potentiels » (entreprises qui embauchent des alternants sans offre publiée = exactement le concept d'opportunité cachée) | ✅ | Alternance ≠ stage, mais très pertinent pour des M1/M2. Excellent pour calibrer le rapprochement nom↔SIRET | 📄 → **jeton à créer** |
| **ATS publics** : Greenhouse (`boards-api.greenhouse.io/v1/boards/{slug}/jobs`), Lever (`api.lever.co/v0/postings/{slug}`), SmartRecruiters (`api.smartrecruiters.com/v1/companies/{id}/postings`), Recruitee (`{slug}.recruitee.com/api/offers`), Workable, Teamtailor | Libre, sans clé | Offres **complètes** (description intégrale, type de contrat dont stage) par entreprise | ❌ (on part de l'entreprise, donc rapprochement trivial) | Il faut connaître le *slug* de chaque entreprise → utile pour enrichir les ~100 meilleures cibles, pas pour un balayage. Couvre surtout startups et scale-ups | 📄 |
| **API Offres d'emploi France Travail** | ⚠️ suspendue | Offres actives + code ROME + `secteurActivite` + tranche d'effectif | ❌ | Voir ci-dessus | ⚠️ |
| Export de stages d'une école | Sur demande | Vérité terrain pour valider le score | Nom → à rapprocher | **Hors périmètre** (l'appli est nationale, pas propre à l'ENSAI) → cité comme perspective | ➖ |
| Choisir le service public / place de l'emploi public | Site public, pas d'API documentée trouvée | Offres data du secteur public (INSEE, collectivités, CHU) | — | À vérifier | ❓ |
| ~~LinkedIn, Indeed, Welcome to the Jungle, JobTeaser~~ | Exclus (CGU, pas d'API) | — | — | — | ❌ |

## 2. Référentiel entreprises

| Source | Accès | Apport | Statut |
|---|---|---|---|
| **API Recherche d'entreprises** (recherche-entreprises.api.gouv.fr) | Libre, sans clé, ~7 req/s | `/search` (filtres département, NAF, tranche d'effectif) et **`/near_point?lat&long&radius`** (recherche par rayon !). Renvoie SIREN/SIRET, NAF, tranche d'effectif + année, catégorie (PME/ETI/GE), lat/lon, **`finances` {année: CA, résultat net}**, nombre d'établissements, Egapro, IDCC. ⚠️ Renvoie aussi les dirigeants (données perso) → ne pas les afficher | ✅ testé. Dans un rayon de 20 km autour de Rennes : 2 619 établissements en 62.01Z, 1 657 en 62.02A, 5 744 en 70.22Z (micro-entreprises comprises → filtrer sur l'effectif) |
| **Stock SIRENE géolocalisé** (data.gouv, parquet) | Téléchargement libre | Même info en masse, hors ligne → **cache Bretagne** robuste pour la démo, sans dépendance réseau | 📄 |
| **Ratios financiers BCE/INPI** (data.economie.gouv.fr) | Libre | CA et marges multi-annuels par SIREN → **croissance du CA** | 📄 ⚠️ fichiers signalés vides fin 2024, à revérifier |
| **BODACC** (opendatasoft) | Libre, sans clé | Procédures collectives → **exclure les entreprises en difficulté** | ✅ testé (44 490 annonces de procédures collectives dans le 35) |
| **Index Egapro** | Libre | Signal « ≥ 50 salariés », structure RH | 📄 (aussi dans Recherche d'entreprises) |
| Site web / page carrière | ❌ pas de source ouverte fiable | Manque connu → recherche manuelle ou API de recherche web pour le top 50 | ⚠️ |

## 3. Signal d'embauche et marché du travail

| Source | Accès | Apport | Statut |
|---|---|---|---|
| **API La Bonne Boîte** (francetravail.io) | Classée « accès ouvert » sur data.gouv, mais une source communautaire signale une habilitation manuelle (erreur 403 sinon) | Probabilité d'embauche par SIRET et métier ROME | 📄 → **à demander tout de suite** |
| **API Marché du travail** (francetravail.io) | Accès ouvert, compte francetravail.io | Tension et volume d'offres par métier et territoire → contexte (« le métier data scientist est tendu en Bretagne ») | 📄 |
| **API ROME 4.0** | Accès ouvert | Codes ROME et appellations des métiers data (M1403, M1405, M1805…) → dictionnaire de mots-clés pour classer les offres | 📄 |
| **Enquête BMO** (Besoins en main-d'œuvre, France Travail) | Open data | Intentions d'embauche par bassin d'emploi et métier → a priori sectoriel et géographique | 📄 |

## 4. Géographie et transport

| Source | Accès | Apport | Statut |
|---|---|---|---|
| **Géocodage Géoplateforme (BAN)** `data.geopf.fr/geocodage/search` | Libre, sans clé | Adresse saisie → lat/lon | ✅ testé |
| **GTFS STAR Rennes / BreizhGo** (transport.data.gouv.fr) | Libre | Temps de trajet en transports en commun (plus parlant pour un étudiant que la distance à vol d'oiseau) | 📄 |
| openrouteservice / OSRM | Clé gratuite / auto-hébergé | Isochrones voiture et vélo | 📄 |

## 5. Données fournies par l'utilisateur (autorisées)

- **CV (PDF)** → extraction des compétences → adéquation avec les offres de l'entreprise.
- Lettre de motivation générée par un LLM (bonus) à partir du CV et de la fiche entreprise.

## Liens

- [data.gouv – API Offres d'emploi](https://www.data.gouv.fr/dataservices/api-offres-demploi) · [GovAPI Atlas – France Travail](https://govapiatlas.com/fr/org/france-travail/)
- [Adzuna developer](https://developer.adzuna.com/overview) · [limites du quota (source tierce)](https://jobspipe.dev/blog/free-job-api)
- [API La bonne alternance – explorer](https://api.apprentissage.beta.gouv.fr/fr/explorer) · [espace développeurs](https://labonnealternance.apprentissage.beta.gouv.fr/espace-developpeurs)
- [API La Bonne Boîte (data.gouv)](https://www.data.gouv.fr/dataservices/api-la-bonne-boite)
- [Ratios financiers BCE/INPI](https://www.data.gouv.fr/datasets/ratios-financiers-bce-inpi)
