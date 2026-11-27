# Projet — Radar

> Document de référence : le « pourquoi » et le « quoi ». À relire quand on hésite sur une priorité.

## Équipe

| Prénom | Rôle (voir `TACHES.md`) | Journal |
|---|---|---|
| Mathis | _TBD_ | [journal](journal/mathis.md) |
| Celia | _TBD_ | `journal/celia.md` |
| Maxence | _TBD_ | `journal/maxence.md` |
| Emma | _TBD_ | `journal/emma.md` |

## Contexte

Hackathon étudiant ENSAI, thème : **« une application qui change la vie des étudiants »**.
Contrainte forte : l'appli doit marcher dès la démo **sans données saisies par les utilisateurs**. On n'utilise que l'open data, les API publiques ou les documents fournis par l'utilisateur lui-même (son CV).

## Problème

Les stages data intéressants sont rarement publiés. Les étudiants candidatent sur les mêmes offres visibles, alors que beaucoup d'entreprises proches recrutent des profils data sans publier d'offre de stage. Ce sont les meilleures cibles pour une **candidature spontanée**, mais personne ne sait les trouver.

## Solution : Radar

Trouver les entreprises proches de l'étudiant qui ont un **besoin dans son domaine** (elles recrutent ces profils) mais **pas d'offre visible pour le contrat qu'il cherche** (stage ou alternance) → les classer et expliquer pourquoi.

- **Échelle : France entière**, pour tous les étudiants, pas seulement ceux de l'ENSAI.
- **Domaine paramétrable** (data par défaut pour la démo ; finance, marketing, informatique… via les codes ROME et des mots-clés).
- **Contrats** : on collecte stages, alternances et emplois. Les offres d'emploi servent de signal de besoin ; le stage ou l'alternance est ce que l'étudiant vise.

### Parcours utilisateur
1. L'étudiant saisit une ville ou une adresse, un rayon, son domaine, le contrat visé (stage ou alternance), et éventuellement des secteurs et une taille d'entreprise (et, en option, il dépose son CV).
2. Il obtient une carte et une liste d'entreprises classées par score.
3. Chaque entreprise a une fiche : décomposition du score (pourquoi elle est recommandée), offres data récentes, effectif, croissance, liens.
4. Bonus : génération d'une lettre de candidature spontanée personnalisée (LLM).

### Cœur statistique (différenciation)
- **Intensité data** : part des offres de l'entreprise qui sont des offres data, rétrécie vers la moyenne de son secteur NAF par un modèle bêta-binomial (bayésien empirique). Une entreprise avec 1 offre data sur 1 ne passe donc pas devant une entreprise avec 8 sur 10.
- **Opportunité cachée** : recrute des profils data, mais aucune offre de stage visible.
- **Dynamisme** : croissance (CA, effectif), probabilité d'embauche.
- **Adéquation** : distance ou temps de trajet, secteur, taille, compétences du CV.
- **Score** : combinaison pondérée, poids réglables par l'utilisateur, chaque contribution affichée.
- **Modèle de réponse (démonstrateur)** : probabilité qu'une entreprise réponde à une candidature spontanée. Les entreprises et leurs variables sont **réelles** ; seules les réponses sont **simulées**, selon une règle paramétrique documentée, faute de données ouvertes sur ces réponses. On montre que la chaîne fonctionne (calibration, AUC, paramètres retrouvés). Elle sera réentraînée sur de vrais retours d'utilisateurs après le lancement. **Toujours affiché comme simulé** dans l'app et les slides.

### Ce qui nous distingue de La Bonne Boîte
La Bonne Boîte prédit des embauches en CDI/CDD pour les demandeurs d'emploi, par métier, à partir des déclarations d'embauche. Elle ne mesure ni la **maturité data** d'une entreprise, ni les **stages**, et n'explique pas son score. Radar s'adresse aux étudiants, mesure le besoin data, explique chaque recommandation et peut utiliser La Bonne Boîte comme simple variable d'entrée.

## Livrables

- [ ] Application démo (Streamlit), France entière, sur des données pré-calculées
- [ ] Slides de pitch (avec la méthodologie du score et ses limites)
- [ ] Code reproductible (pipeline de collecte → scores)

## Données

Voir [`SOURCES.md`](SOURCES.md). ⚠️ L'API Offres d'emploi France Travail est actuellement suspendue.

## Risques connus

- Rapprochement offres ↔ SIRET approximatif (offres anonymes, cabinets) → appariement flou nom + commune, avec **taux de rapprochement affiché**.
- Pas d'historique des offres (24 h : un seul instantané) → le score décrit le marché **aujourd'hui**.
- Quota Adzuna (~250 appels/jour) face à l'échelle nationale → utiliser `top_companies` par département, plus La bonne alternance (nationale, avec SIRET).
- Signal partiel (les stages se publient surtout sur des plateformes sans API) → l'assumer au pitch et croiser plusieurs sources.
- RGPD : pas d'e-mails ni de noms de personnes (les dirigeants sont dans SIRENE : ne pas les afficher), uniquement des sites et pages carrière.

## Critères d'évaluation du jury

- _TBD_

## Planning

| Échéance | Jalon |
|---|---|
| H+2 | Accès aux API, squelette, données factices |
| H+8 | V1 de bout en bout |
| H+16 | V2 (score complet, fiche entreprise) |
| H+18 | Gel des fonctionnalités |
| H+22 | Répétition de la démo |
| H+24 | Pitch |
