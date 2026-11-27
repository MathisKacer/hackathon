# Sources de données — inventaire

> État vérifié le 2026-11-27. ✅ = testé par un appel réel · 📄 = documentation seulement · ⚠️ = point bloquant ou risque.
> Mettre à jour la colonne « Statut » dès que quelqu'un obtient une clé ou teste une source.

## 🚨 Point bloquant : API Offres d'emploi France Travail

**L'API Offres d'emploi n'est plus exposée sur francetravail.io** : France Travail revoit ses conditions de diffusion après des usages massifs par des outils d'IA. L'accès se demande via le formulaire de contact de francetravail.io, sans garantie de délai. **On ne doit pas bâtir la démo dessus.** On fait la demande quand même et, si l'accès arrive, c'est un bonus.
Sources : [data.gouv – API Offres d'emploi](https://www.data.gouv.fr/dataservices/api-offres-demploi), [GovAPI Atlas – France Travail](https://govapiatlas.com/fr/org/france-travail/).

## 1. Offres d'emploi (signal « besoin data »)

| Source | Accès | Ce que ça apporte à Radar | SIRET ? | Fiabilité / limites | Statut |
|---|---|---|---|---|---|
| **Adzuna API** (`/jobs/fr/search`, `/top_companies`) | Clé gratuite (app_id + app_key). Quota gratuit annoncé ~25/min, 250/jour (source tierce). **~10 appels consommés le 2026-11-27** | Champs réels : `id, title, description` (**tronquée ~500 car.**), `company.display_name` (renseigné 50/50), `location` + `latitude/longitude` (50/50), `category` (souvent « Unknown »), **`contract_type` rarement renseigné (14/50)** → stage/alternance à détecter dans le titre/texte, `contract_time`, `created`, `salary_*`, `redirect_url`, `adref`. **Volumes** (2026-11-27) : France toutes offres 1 040 858 ; « data » 35 921 ; « stage data » 812 ; « alternance data » 175 ; Ille-et-Vilaine « data » 508. **`top_companies` ne renvoie que le top 5** → inutilisable pour l'intensité. Offres anciennes présentes (`created` dès 2025-01) → filtrer avec `max_days_old`. Cabinets de recrutement fréquents dans le top (RM Staffing, Talents IT…) → à détecter | ❌ nom seulement | Collecte exhaustive de « data » France ≈ 720 appels (50/page) > quota d'un jour → collecte par région prioritaire, puis le reste. **Le dénominateur « toutes offres de l'entreprise » est hors quota** → intensité modélisée avec l'effectif comme exposition (gamma-Poisson) | ✅ collecteur en place (T12) : **10 776 offres, 2 737 entreprises** le 2026-11-27 (Bretagne, Pays de la Loire, Auvergne-Rhône-Alpes, Occitanie complètes ; Île-de-France 5 000/14 385 ; Nouvelle-Aquitaine partielle). ⚠️ La requête « data » est **bruitée** : « data » n'apparaît que dans **23 % des titres** (le mot est souvent dans la description seule) → le classifieur T13 doit filtrer |
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
| **Stock SIRENE** (INSEE, data.gouv, parquet, mensuel) | Libre, téléchargement direct ; DuckDB lit les fichiers **à distance** (httpfs) sans tout télécharger | 3 fichiers (version de nov. 2026) : [StockEtablissement](https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20261103-101714/stock-stocketablissement-parquet.parquet) (2,2 Go, 44,5 M lignes : siret, NAF, tranche d'effectif + année, commune, état, statut employeur, statut de diffusion) ; [Géolocalisation](https://static.data.gouv.fr/resources/geolocalisation-des-etablissements-du-repertoire-sirene-pour-les-etudes-statistiques/20261123-064215/geoloc-geolocalisationetablissement-sirene-pour-etudes-statistiques-parquet.parquet) (825 Mo : siret → **`y_latitude`, `x_longitude`** en GPS, `qualite_xy`) ; [StockUniteLegale](https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20261103-095402/stock-stockunitelegale-parquet.parquet) (718 Mo : **nom** `denominationUniteLegale`, catégorie PME/ETI/GE). **Volumes** d'établissements actifs : ~17 M (dont 14,9 M sans effectif connu) ; ≥ 1 salarié ~1,9 M ; **≥ 10 salariés (tranche ≥ '11') ~406 k** → filtre retenu, ~50 Mo. ⚠️ Ne pas afficher l'adresse si `statutDiffusionEtablissement = 'P'` ; tranche parfois ancienne (garder `anneeEffectifs`). Une seule personne fait l'extraction et la dépose sur S3 | ✅ schémas lus et comptages faits (40 s à distance) ; **extraction T20 faite** (`radar/collect/sirene.py`, 39 s) : 406 266 établissements, 99,7 % géolocalisés, 0 % sans nom |
| **Ratios financiers BCE/INPI** (data.economie.gouv.fr) | Libre | CA et marges multi-annuels par SIREN → **croissance du CA** | 📄 ⚠️ fichiers signalés vides fin 2024, à revérifier |
| **BODACC** (opendatasoft) | Libre, sans clé | Procédures collectives → **exclure les entreprises en difficulté** | ✅ testé (44 490 annonces de procédures collectives dans le 35) |
| **Index Egapro** | Libre | Signal « ≥ 50 salariés », structure RH | 📄 (aussi dans Recherche d'entreprises) |
| Site web / page carrière | ❌ pas de source ouverte fiable | Manque connu → recherche manuelle ou API de recherche web pour le top 50 | ⚠️ |

## 3. Signal d'embauche et marché du travail

| Source | Accès | Apport | Statut |
|---|---|---|---|
| **API La Bonne Boîte v2** (francetravail.io) | Compte francetravail.io + souscription ; scopes `api_labonneboitev2 search office`. ⚠️ Limite de débit atteinte (HTTP 429) à ~3 req/s → rester à ≤ 1 req/s | `GET /partenaire/labonneboite/v2/recherche?rome=&latitude=&longitude=&distance=&page_size=` → par entreprise : **`siret`**, `company_name`, `naf`, `naf_label`, `location{lat,lon}`, `city`, `department`, **`hiring_potential`** (continu), `is_high_potential`, `headcount_min/max` (souvent 0). Le champ `email` est un simple drapeau oui/non : ne pas l'utiliser. Accepte les codes ROME 4.0. **Couverture faible sur les métiers data fins** (30 km autour de Rennes : M1811 Data engineer = 31, M1403 = 5, M1405 Data scientist = 0, M1419 Data analyst = 0 ; Paris : M1811 = 544, M1403 = 46, M1405 = 3) → interroger un ensemble large de codes (informatique, études) | ✅ testé 2026-11-27 |
| **API Marché du travail** (francetravail.io) | Scopes `api_stats-offres-demandes-emploiv1 offresetdemandesemploi` | Tension et volume d'offres par métier et territoire → contexte (« le métier data scientist est tendu en Bretagne ») | 🟡 jeton OK, endpoint pas encore appelé |
| **API ROME 4.0 – Métiers** | Scopes `api_rome-metiersv1 nomenclatureRome` | `GET /partenaire/rome-metiers/v1/metiers/metier?champs=code,libelle` → 1 923 métiers. Codes data : M1405 Data scientist, M1419 Data analyst, M1811 Data engineer, M1414 Ingénieur statisticien, M1403 Chargé d'études socio-éco, M1423 Chief Data Officer, M1824/M1851/M1872 BI, M1889 Ingénieur IA, M1868 Architecte BDD, K2403 Biostatisticien, C1105/C1120 Actuariat, M1430 Études commerciales → base de `domains.yaml` | ✅ testé |
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
