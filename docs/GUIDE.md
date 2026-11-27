# Guide des fonctionnalités : interface, recherche d'entreprises, comptes, historique, sécurité, SIRENE, BODACC, fiche entreprise

> **Mode d'emploi** des parties construites par @celia : à quoi elles servent, comment les utiliser, comment elles marchent, comment les régler, et ce qu'on peut faire ensuite.
> Pour le reste de l'app (carte, score, poids, P(réponse)) : `ARCHITECTURE.md` et les décisions D19 à D23.
> Mettre à jour ce guide quand on change une de ces fonctionnalités.
>
> **L'interface a changé (D30)** : 3 pages, voir la section 0 ci-dessous.

## Sommaire

0. [L'interface : 3 pages (T56, D30)](#0-linterface--3-pages-t56-d30)
1. [Vue d'ensemble](#1-vue-densemble)
2. [Référentiel des entreprises (SIRENE, T20)](#2-référentiel-des-entreprises-sirene-t20)
3. [Entreprises en difficulté (BODACC, T23)](#3-entreprises-en-difficulté-bodacc-t23)
4. [Comptes facultatifs et profil (T48)](#4-comptes-facultatifs-et-profil-t48)
5. [Historique des recherches (T49)](#5-historique-des-recherches-t49)
6. [Sécurité des mots de passe (D16)](#6-sécurité-des-mots-de-passe-d16)
7. [Où sont les données ?](#7-où-sont-les-données-)
8. [Commandes utiles](#8-commandes-utiles)
9. [Ce qu'on peut faire ensuite](#9-ce-quon-peut-faire-ensuite)
10. [Fiche entreprise (T43, T38)](#10-fiche-entreprise-t43-t38)
11. [La Bonne Boîte dans la couche orange (T28, T29, D27)](#11-la-bonne-boîte-dans-la-couche-orange-t28-t29-d27)
12. [Recherche d'entreprises (page Entreprises)](#12-recherche-dentreprises-page-entreprises)
13. [Favoris (T54)](#13-favoris-t54)
14. [Entreprise et sites (T57)](#14-entreprise-et-sites-t57)

---

## 0. L'interface : 3 pages (T56, D30)

**Navigation.** Une barre en haut de l'écran avec trois pages (plus de barre latérale) :

| Page | Pour quoi faire | Fichier |
|---|---|---|
| **Explorer** (page d'accueil) | Chercher où candidater autour de soi | `app/vues/explorer.py` |
| **Entreprises** | Chercher une entreprise précise et voir sa fiche | `app/vues/entreprises.py` |
| **Se connecter** / **Mon espace (prénom)** | Compte facultatif, profil, historique des recherches | `app/vues/mon_espace.py` |

**Explorer, de haut en bas :**
1. **La recherche** : « Où ? » (suggesteur de ville, T55 : on tape le début du nom et on choisit « Ville (code postal) »), « Contrat » (Tous / Stage / Alternance / Emploi), « Domaine », « Rayon ».
2. **Le bouton « Filtres »** : un panneau avec les régions, le mot-clé, l'ancienneté des offres, la taille et le secteur des entreprises, « Afficher aussi les entreprises en liquidation », le classement (score ou chance de réponse) et l'importance de chaque critère du score. Le bouton affiche le nombre de filtres actifs (« Filtres (2) »).
3. **Une phrase de résultat** : « Autour de Rennes (35000) (20 km) : 42 entreprises pourraient t'accueillir en alternance sans avoir publié d'offre, et 18 offres sont publiées. » Sans ville : un « Comment ça marche » en 3 étapes.
4. **La carte** : offres en bleu, candidatures spontanées en orange (`app/carte.py`, inchangé).
5. **Deux onglets** : « Candidatures spontanées » (Entreprise, Lieu, Distance, Autres sites, Taille, Situation, La Bonne Boîte ✔, Score, **Chance de réponse** — estimation issue de réponses simulées, expliquée en info-bulle, D31) et « Offres » (lien vers chaque annonce).
6. **Un clic sur une ligne** de « Candidatures spontanées » ouvre la **fiche dans une fenêtre** par-dessus la page (section 10). Fermer la fenêtre permet d'en ouvrir une autre.

**Principes.**
- Textes courts, en français simple : pas de numéros de tâches, de noms de fichiers ni de commandes à l'écran (ils restent dans les commentaires du code).
- Peu d'emojis : seulement les drapeaux d'alerte et le ✔ La Bonne Boîte.
- **Les réglages sont conservés quand on change de page** (`persist_widget_state` dans `app/commun.py`).
- **Thème sobre** (`.streamlit/config.toml`) : bleu nuit `#1D3557`, fond `#FAFAF7`, police Inter ; le bleu et l'orange restent réservés à la carte.

**Organisation du code.**

| Fichier | Rôle |
|---|---|
| `app/streamlit_app.py` | point d'entrée : configuration, navigation |
| `app/commun.py` | constantes, chargement des données (mis en cache), réglages du profil (`WIDGET_KEYS`, `profile_keys()`, `PROFILE_LABELS`, `init_defaults()`) |
| `app/carte.py` | carte folium et popup des entreprises |
| `app/fiche_ui.py` | fiche entreprise (`open_fiche` : fenêtre) |
| `app/compte.py` | comptes : formulaires, `record_search`, page Mon espace |

**Ajouter un réglage de recherche** : suivre la consigne de `CLAUDE.md` (widget avec une `key` dans Explorer, puis `WIDGET_KEYS`, `profile_keys()`, `PROFILE_LABELS`, `init_defaults()` dans `app/commun.py`).

---

## 1. Vue d'ensemble

| Fonctionnalité | Tâche | Ce que voit l'utilisateur | Fichiers principaux | Décision |
|---|---|---|---|---|
| Référentiel des entreprises | T20 | Les entreprises de la couche orange : nom, secteur, taille, adresse, position | `radar/collect/sirene.py`, `scripts/extract_sirene.py` | D12 |
| Entreprises en difficulté | T23 | Drapeau 🟡/🟠/🔴, score réduit, liquidations masquées | `radar/collect/bodacc.py`, `radar/procedures.py` | D24 |
| Comptes facultatifs + profil | T48 | « Se connecter / Créer un compte » ; réglages retrouvés à la connexion | `radar/accounts.py`, `app/compte.py` | D14 |
| Historique des recherches | T49 | « 🕘 Mes recherches » avec « ↻ Relancer » | `radar/accounts.py`, `app/compte.py` | D14 |
| Sécurité des mots de passe | — | Règles affichées, blocage après 5 échecs | `radar/accounts.py`, `docs/SECURITE.md` | D16 |
| Fiche entreprise | T43 | « 🔎 Fiche entreprise » sous la liste orange : tout sur une entreprise | `radar/fiche.py`, `app/fiche_ui.py` | — |

Principe commun : **la démo marche sans rien configurer**, en mode anonyme, et chaque fonctionnalité se règle en un seul endroit du code.

---

## 2. Référentiel des entreprises (SIRENE, T20)

**À quoi ça sert.** La liste des entreprises candidates pour la couche orange « Candidature spontanée » : tous les établissements actifs d'au moins 10 salariés en France.

**Comment ça marche.**
- DuckDB lit **à distance** les trois fichiers SIRENE de data.gouv (établissements, unités légales, géolocalisation) et la nomenclature NAF, sans télécharger les ~3,7 Go : seules les colonnes utiles sont lues.
- Filtre : établissement actif, tranche d'effectif ≥ 10 salariés (le code `'NN'`, effectif inconnu, est exclu), nomenclature NAF rév. 2.
- Résultat : **406 266 établissements** (278 950 entreprises), 99,7 % géolocalisés, 100 % avec un nom, dans `data/processed/entreprises.parquet` (~26 Mo).
- Le nom affiché est celui de l'entreprise (unité légale), sinon celui de l'établissement, sinon prénom + nom pour un entrepreneur individuel.
- Respect de la vie privée : position et adresse **masquées** pour les établissements en diffusion partielle (`diffusion_partielle`).

**Colonnes utiles en plus du contrat :** `effectif_min`, `effectif_max`, `effectif_estime` (utilisé par le rapprochement T21), `tranche_libelle` (« 20 à 49 salariés »), `adresse`, `departement`, `naf_section`, `naf_division`, `siege`…

**Utiliser.**
```bash
uv run python scripts/extract_sirene.py            # France entière, ~2 min
uv run python scripts/extract_sirene.py --dep 35   # un département, pour tester vite
```

**Régler.** URL des fichiers SIRENE (à changer au prochain millésime) en tête de `radar/collect/sirene.py` ; seuil d'effectif : `MIN_TRANCHE_EFFECTIF` dans `radar/config.py`.

**Histoire.** T20 a été faite deux fois en parallèle (Celia et Mathis) parce qu'un push était bloqué ; les deux versions ont été fusionnées (D12) en gardant le meilleur de chacune.

---

## 3. Entreprises en difficulté (BODACC, T23)

**À quoi ça sert.** Ne pas recommander une entreprise en faillite sans le dire. On **pénalise et on signale, sans supprimer** (D24) : une entreprise en sauvegarde ou sous plan continue de fonctionner, et à terme Radar veut recenser un maximum d'entreprises avec leur situation.

**Ce que voit l'utilisateur dans la couche orange :**

| Situation | Drapeau | Effet |
|---|---|---|
| Sauvegarde (difficultés anticipées, le dirigeant garde la main) | 🟡 | score légèrement réduit |
| Plan adopté (sauvegarde ou redressement : l'entreprise poursuit) | 🟡 | score légèrement réduit |
| Redressement judiciaire (cessation des paiements, activité sous contrôle du tribunal) | 🟠 | score nettement réduit, surtout pour l'alternance et l'emploi |
| Liquidation judiciaire (activité en principe arrêtée) | 🔴 | score très réduit et **masquée par défaut** ; case « Afficher aussi les entreprises en liquidation » |

L'alerte apparaît dans la colonne « Situation » de la liste et dans la fiche de la carte, avec la date et un lien vers l'annonce BODACC.

**Comment ça marche.**
1. `radar/collect/bodacc.py` télécharge en un seul export les annonces « procédures collectives » des **2 dernières années** (~405 000 annonces, 47 Mo, ~1 min) et les garde en cache dans `data/raw/bodacc_collectives.parquet`.
2. Chaque annonce est classée d'après la nature du jugement (`classify_nature`) : sauvegarde, redressement, liquidation (y compris clôture pour insuffisance d'actif et plan de cession), plan, fin (procédure close sans liquidation), ou ignorée (état des créances, interdiction de gérer…).
3. Pour chaque SIREN, on garde le **dernier événement qui change la situation**. Une procédure terminée (« fin ») ne donne pas d'alerte.
4. Les colonnes `procedure_type`, `procedure_date`, `procedure_nature`, `procedure_url` et `procedure_collective` sont ajoutées à `entreprises.parquet` (par SIREN : tous les établissements de l'entreprise).
5. Dans la couche orange, `rank_spontaneous` (`radar/spontaneous.py`) appelle `apply_procedures` (`radar/procedures.py`) : score × coefficient, colonne `alerte`, liquidations retirées sauf si la case est cochée.

**Chiffres.** 11 124 établissements en alerte sur 406 266 (2,7 %) : 6 130 liquidations, 2 449 redressements, 2 046 plans, 499 sauvegardes.

**Coefficients appliqués au score** (dans `PENALTIES`, `radar/procedures.py`) :

| | stage | alternance | emploi |
|---|---|---|---|
| sauvegarde, plan | ×0,85 | ×0,75 | ×0,75 |
| redressement | ×0,6 | ×0,4 | ×0,4 |
| liquidation | ×0,1 | ×0,05 | ×0,05 |

Pourquoi selon le contrat : une alternance ou un emploi engage bien plus l'entreprise (contrat long, salaire) qu'un stage. Rappel : un stage de plus de 2 mois est obligatoirement gratifié en France, donc on ne distingue pas stages rémunérés et non rémunérés.

**Utiliser.**
```bash
uv run python scripts/collect_bodacc.py            # utilise le cache s'il existe
uv run python scripts/collect_bodacc.py --refresh  # retélécharge les annonces (données du jour)
uv run python scripts/build_all.py                 # le pipeline complet l'inclut (étape « 1 bis »)
```

**Régler.** Coefficients : `PENALTIES` ; drapeaux et phrases : `ALERTS` (tous deux dans `radar/procedures.py`) ; fenêtre de temps : `PERIOD_YEARS` ; classement des jugements : `_RULES` (dans `radar/collect/bodacc.py`).

**Limites** (L21–L23) : 2 ans d'historique seulement ; tous les établissements d'une entreprise en procédure sont signalés ; coefficients fixés à dire d'expert.

---

## 4. Comptes facultatifs et profil (T48)

**À quoi ça sert.** Retrouver ses réglages de recherche d'une visite à l'autre, sans rendre la connexion obligatoire.

**Ce que voit l'utilisateur.**
- Par défaut : mode anonyme, rien n'est enregistré ; la page s'appelle « **Se connecter** ».
- Page **Se connecter** : onglets **Connexion** et **Créer un compte**. À la création, les réglages actuels deviennent le profil.
- Connecté, la page devient « **Mon espace (prénom)** » : « Enregistrer mes réglages », « Se déconnecter », le profil enregistré, l'historique (section 5) et « Supprimer mon compte » (case à cocher de confirmation ; efface compte, profil et historique).
- À la connexion, tous les réglages reviennent : ville, rayon, domaine, contrat, régions, mot-clé, taille, secteur, poids du score, classement, « afficher les liquidations »…

**Comment ça marche.**
- `radar/accounts.py` : la partie serveur (comptes, mots de passe, profils, historique) dans une base SQLite. Testable sans Streamlit.
- `app/compte.py` : formulaires (`login_forms`), enregistrement des recherches (`record_search`), page Mon espace (`account_page`). Les anciennes fonctions de barre latérale (`account_sidebar`, `search_history`) restent pour les tests.
- **Le profil = les valeurs des widgets de recherche** listés dans `profile_keys()` (`app/commun.py`). Chaque widget a une `key` ; à la connexion, le profil est recopié dans `st.session_state`. Une valeur devenue invalide (région disparue des données…) est ignorée.

**⚠️ Règle pour ajouter un réglage à l'app** : voir `CLAUDE.md` et la section 0.

Sinon le réglage n'est pas enregistré dans le profil.

---

## 5. Historique des recherches (T49)

**Ce que voit l'utilisateur (connecté seulement).** Page **Mon espace**, partie « Mes recherches » : pour chaque recherche, la date, un résumé lisible (« Contrat : Stage · Régions : Bretagne »), le nombre de résultats et les premières entreprises. Bouton « Relancer » (remet tous les réglages **et ramène sur Explorer**) et « Effacer mon historique ». En anonyme, rien n'est enregistré.

**Comment ça marche.**
- `record_search(...)` est appelée par Explorer **après** le calcul des résultats ; Mon espace affiche la liste.
- Streamlit relance la page à chaque changement de réglage : pour ne pas créer une entrée par cran de curseur, les changements faits **à moins de 2 minutes** de la dernière recherche la mettent à jour. Une recherche identique à la précédente n'est pas dupliquée. **50 recherches max** par compte.
- « Relancer » passe par un rappel `on_click` (qui remplit les réglages) puis `st.switch_page` vers Explorer.
- `top=` reçoit les **noms** des premières entreprises (affichés tels quels), pas les SIRET.

**Régler.** `SEARCH_MERGE_WINDOW`, `SEARCH_MAX_PER_USER`, `SEARCH_TOP_MAX` dans `radar/accounts.py` ; nombre affiché : `HISTORY_SHOWN` dans `app/compte.py`.

---

## 6. Sécurité des mots de passe (D16)

Détails complets, justification et références (CNIL, NIST) : **`docs/SECURITE.md`**. En bref :

- **Choix du mot de passe** : au moins 12 caractères et 3 types parmi minuscules, majuscules, chiffres, caractères spéciaux (l'espace compte : les phrases de passe passent) ; mots de passe courants refusés ; identifiant interdit dans le mot de passe ; le message dit exactement ce qui ne va pas.
- **Stockage** : jamais en clair ; haché avec **scrypt** et un sel aléatoire par compte ; comparaison à temps constant.
- **Connexion** : après **5 échecs**, compte bloqué **15 minutes**, même en rechargeant la page ; un identifiant inconnu répond dans le même temps qu'un identifiant existant.
- **Données personnelles** : pas d'e-mail, pas de nom ; « Supprimer mon compte » efface tout.
- **Ce qui manque** (assumé) : double authentification, vérification des mots de passe fuités, « mot de passe oublié », « se souvenir de moi ».

Pour tester : `motdepasse1` est refusé, `Radar-Demo-2026` est accepté.

---

## 7. Où sont les données ?

| Donnée | Fichier | Dans Git ? | Comment l'obtenir |
|---|---|---|---|
| Entreprises (SIRENE + BODACC) | `data/processed/entreprises.parquet` | non | `extract_sirene.py` puis `collect_bodacc.py` (ou `build_all.py`) |
| Annonces BODACC (cache) | `data/raw/bodacc_collectives.parquet` | non | `collect_bodacc.py` |
| Comptes, profils, historique | `data/app/radar.db` | **jamais** | créé à la première création de compte |

**La base des comptes est un simple fichier SQLite**, sans serveur de base de données : l'app l'ouvre et y écrit directement. Elle est sur le disque persistant du service VS Code Onyxia :
- conservée quand on relance l'app ou qu'on met le service en pause ;
- **perdue si le service est supprimé** ;
- **une base par membre de l'équipe** : un compte créé chez l'un n'existe pas chez l'autre. Pour la démo, créer les comptes **sur le pod qui sert à la présentation**.

Détails : `docs/SECURITE.md` › « Où est la base ? ».

---

## 8. Commandes utiles

```bash
uv run python scripts/extract_sirene.py [--dep 35]    # référentiel entreprises (T20)
uv run python scripts/collect_bodacc.py [--refresh]   # entreprises en difficulté (T23)
uv run python scripts/build_all.py                     # tout reconstruire (SIRENE, BODACC, offres, scores…)
uv run streamlit run app/streamlit_app.py              # lancer l'app → <URL du service>/proxy/8501/

uv run pytest -q tests/test_sirene.py                  # tests SIRENE
uv run pytest -q tests/test_bodacc.py                  # tests BODACC (28)
uv run pytest -q tests/test_accounts.py tests/test_compte_ui.py   # tests comptes, historique, sécurité
rm data/app/radar.db                                   # repartir de zéro côté comptes
```

---

## 9. Ce qu'on peut faire ensuite

Par ordre d'intérêt (✅ = déjà une tâche dans `TACHES.md`) :

| Idée | Intérêt | Effort | Tâche |
|---|---|---|---|
| **Fiche entreprise** : enrichir avec le chiffre d'affaires (T22), le site web, la carte de l'établissement | Va vers « tout savoir sur une entreprise dès qu'on la cherche » | faible | T43 fait, suite avec T22 |
| **Rechercher une entreprise par son nom** et voir toutes ses infos (recrutement en cours, situation, score) | Vision à terme : recenser un maximum d'entreprises | moyen | à créer |
| **Suivi des candidatures** (envoyée, relancée, réponse) dans le compte | Fournirait de **vraies réponses** pour remplacer les réponses simulées du modèle (D6) | moyen | à créer |
| Base des comptes **hébergée** (Supabase, région UE) avec repli sur SQLite | Comptes partagés et sauvegardés | 1 h 30–2 h | ✅ T52 (très optionnel) |
| « Mot de passe oublié » et « se souvenir de moi » | Confort | moyen (demande un e-mail ou un cookie signé) | avec T52 |
| BODACC : rattacher les entrepreneurs du répertoire des métiers, élargir la fenêtre, actualiser chaque jour | Couverture plus complète | faible | — |
| Estimer les coefficients BODACC sur de vraies réponses | Pénalité justifiée par les données, plus à dire d'expert | dépend du suivi des candidatures | — |
| Données financières (chiffre d'affaires) pour la composante « dynamisme » | Score plus riche | moyen (fichiers INPI à vérifier) | ✅ T22 |

**Pour le pitch** : « Pas de compte obligatoire ; mots de passe hachés et règles CNIL ; entreprises en difficulté signalées d'après le BODACC, avec une pénalité qui dépend du contrat visé ; tout est réglable et expliqué. »

---

## 10. Fiche entreprise (T43, T38)

**À quoi ça sert.** Voir d'un coup d'œil tout ce qu'on sait d'une entreprise de la couche orange, et **pourquoi** elle est recommandée. Premier pas vers « tout savoir sur une entreprise dès qu'on la cherche ».

**Ce que voit l'utilisateur.** Une **fenêtre** par-dessus la page, ouverte par un clic sur une ligne de « Candidatures spontanées » (Explorer) ou d'un résultat de recherche (Entreprises). Depuis la recherche, l'entreprise n'a ni distance ni score final : le bloc « Pourquoi elle est recommandée » est masqué, le reste est affiché. Contenu :

| Bloc | Contenu | D'où ça vient |
|---|---|---|
| Identité | nom, établissement, secteur, taille, catégorie (PME, ETI, grande entreprise), siège ou non ; **alerte** si procédure collective | SIRENE (T20), BODACC (T23) |
| Pourquoi elle est recommandée | phrase « Recommandée car… » si la colonne `explication` existe (T32, Mathis) ; score, distance, P(réponse) simulée ; **décomposition du score** en barres (apport de chaque composante) | score (T30, T42), T32, T37 |
| Besoin dans le domaine | **La Bonne Boîte** (T38) : « ✔ Signalée par La Bonne Boîte (France Travail) comme susceptible d'embaucher en … », avec le potentiel d'embauche (médiane 2,8), sinon « potentiel estimé » ; **niveau de preuve** (🟢 élevé ≥ 5 offres, 🟡 moyen 1 à 4, ⚪ faible 0, ⚪ non collecté si la zone n'a pas été collectée) ; offres du domaine dont stages et alternances ; intensité estimée (offres pour 100 salariés) avec **intervalle crédible à 90 %** et moyenne du secteur | `scores.parquet` (D13) |
| Offres récentes | jusqu'à 10 offres de l'entreprise (toute l'entreprise, par SIREN ; sans les intermédiaires), avec lien vers l'annonce | `offres.parquet` (T13, T21) |
| Situation (BODACC) | historique de toutes les annonces de procédure collective sur 2 ans, avec lien | cache BODACC (T23) |
| Coordonnées et liens | adresse (masquée si diffusion partielle), SIRET, SIREN ; liens Annuaire des entreprises, OpenStreetMap, annonce BODACC | SIRENE |

**Comment ça marche.**
- `radar/fiche.py` (données, testable sans Streamlit) : chaque fonction lit **un seul** établissement avec DuckDB (`load_company`, `company_offers`, `bodacc_history`), calcule le niveau de preuve (`evidence`) et les liens (`links`). Si un fichier manque (pas d'offres, pas de cache BODACC), le bloc correspondant est simplement vide.
- `radar/fiche.py` aussi : `load_scores` (indicateurs du domaine pour une entreprise trouvée par la recherche) et `hiring_signal` (La Bonne Boîte ou estimation, T38).
- `app/fiche_ui.py` (affichage) : `open_fiche(siret, ligne, domaine)` ouvre la fenêtre (`st.dialog`) ; `fiche_content` dessine la fiche. À la fermeture, la sélection de la liste est vidée pour pouvoir rouvrir la même fiche. Résultats mis en cache (`st.cache_data`). L'ancien panneau avec sélecteur (`render_fiche`) reste pour les tests.
- **Coordination avec T32** : le popup de la carte est à Mathis ; ce panneau à Celia ; la fiche affiche la colonne `explication` dès qu'elle existe.

**Régler.** Nombre d'offres : `OFFERS_SHOWN` ; seuils du niveau de preuve : `evidence` (`radar/fiche.py`).

**Tests.** `uv run pytest -q tests/test_fiche.py` (8 tests, dont l'affichage et La Bonne Boîte avec AppTest).

## 11. La Bonne Boîte dans la couche orange (T28, T29, D27)

**À quoi ça sert.** Montrer qu'une entreprise est signalée par **France Travail (La Bonne Boîte)** comme susceptible d'embaucher sur un métier data, d'après les déclarations d'embauche réelles. C'est la composante « **Potentiel d'embauche** » du score (`c_embauche`).

**Ce que voit l'utilisateur.**
- Curseur « Potentiel d'embauche » (ancien nom : « Besoin attendu »), avec une aide qui explique la règle.
- Dans la liste orange, une colonne **« La Bonne Boîte »** avec ✔ pour les établissements signalés (la colonne n'apparaît que s'il y en a au moins un).
- Dans la fenêtre de la carte : « ✔ Signalée par La Bonne Boîte (France Travail) (potentiel x) ».

**Comment ça marche.**
- `scripts/collect_lbb.py` → `data/raw/lbb.parquet` (1 736 établissements data en France, 30 appels) ; `build_all.py` → `scores.parquet` avec `c_embauche_source` (`la_bonne_boite` / `proxy_besoin_attendu`) et `lbb_potentiel` (`radar/score/embauche.py`).
- `radar/spontaneous.py › signaled_by_lbb(df)` : vrai si `c_embauche_source == "la_bonne_boite"`, faux partout si la colonne manque (anciens scores, données factices) → pas d'erreur, pas de colonne.
- Limite : La Bonne Boîte ne couvre que 0,3 % des établissements du référentiel (L11) ; autour de Rennes, quelques dizaines.

---

## 12. Recherche d'entreprises (page Entreprises)

**À quoi ça sert.** Trouver une entreprise précise et voir sa fiche, **dans toute la France** (les ~406 000 établissements d'au moins 10 salariés), pas seulement autour de sa ville. Va vers l'idée « tout savoir sur une entreprise dès qu'on la cherche ».

**Ce que voit l'utilisateur.** Une barre « Nom de l'entreprise, SIREN ou SIRET » et un champ facultatif « Ville ou code postal » (début du nom de la commune, ou début du code postal : « 35 » = Ille-et-Vilaine). Jusqu'à 50 établissements, les plus proches de la recherche d'abord, puis les plus gros. Colonnes : Entreprise, Lieu, Taille, Activité, Situation (BODACC). **Un clic ouvre la fiche** en fenêtre.

**Ce qu'elle tolère.**

| Recherche | Résultat |
|---|---|
| `sopra steria`, `SOPRA-STERIA` | Sopra Steria (casse, tirets, accents ignorés) |
| `sopra steira`, `spora steria` | Sopra Steria (fautes de frappe) |
| `insee` | l'Institut national de la statistique (sigle) |
| `orane` + ville `rennes` | les établissements d'Orange à Rennes |
| `552081317` (SIREN) ou un SIRET | tous les établissements de l'entreprise, ou l'établissement |

**Comment ça marche** (`radar/recherche.py`, testable sans Streamlit) :
1. **Index** chargé une fois (~7 s, puis en mémoire) : nom de l'entreprise + nom de l'établissement + sigle, **normalisés** (minuscules, sans accents ni ponctuation), et commune normalisée.
2. **Présélection rapide** : les noms qui contiennent les 3 premières lettres de **chaque** mot recherché.
3. **Note fine, mot par mot** : pour chaque mot recherché, la meilleure ressemblance avec un mot du nom (`rapidfuzz`), puis la moyenne. « sopra steira » / « sopra steria group » ≈ 92 ; « sopra » seul ≈ 68 (écarté sous 75).
4. **Secours** si rien n'est assez proche (faute dans les premières lettres) : il suffit qu'**un** des mots soit reconnu pour être candidat.
5. SIREN (9 chiffres) ou SIRET (14 chiffres) : recherche exacte.

Temps de réponse : 0,05 à 0,4 s.

**Régler.** Seuil de ressemblance : `MIN_SCORE` (75) ; colonnes chargées : `INDEX_COLS` (`radar/recherche.py`) ; nombre de résultats : `limit` (50, `app/vues/entreprises.py`).

**Tests.** `uv run pytest -q tests/test_recherche.py` (fautes, accents, sigle, ville, SIREN/SIRET, résultat vide).

**Suites possibles.** Rechercher aussi par activité (« conseil informatique Rennes ») ; regrouper les établissements d'une même entreprise ; ouvrir directement la fiche depuis la carte.

---

## 13. Favoris (T54)

**À quoi ça sert.** Garder les entreprises et les offres qui intéressent, et suivre ses candidatures : « je repère, je retrouve plus tard, je note où j'en suis ».

**Ce que voit l'utilisateur.**
- **Entreprise** : bouton « ☆ Ajouter aux favoris » / « ★ Dans mes favoris » dans sa **fiche** (la fenêtre ouverte depuis Explorer ou Entreprises). Dans la liste « Candidatures spontanées », une colonne ★ montre celles déjà en favori.
- **Offre** : une **case ★** sur chaque ligne de la liste « Offres » (Explorer).
- **Mon espace › Mes favoris** : deux onglets, Entreprises et Offres. Pour chaque favori : « Voir la fiche » (entreprise) ou « Voir l'offre » (lien vers l'annonce), « Retirer », la case **« Candidaté »** et une **note libre** (contact, date de relance…). Une offre qui n'est plus dans les données est marquée « n'est plus en ligne » mais reste en favori.

**Sans compte ou avec un compte** (choix fait avec l'équipe) :

| | Sans compte | Avec un compte |
|---|---|---|
| Mettre des favoris | oui, **temporaires** (le temps de la visite) | oui, enregistrés |
| Où c'est gardé | en mémoire (`st.session_state`), **rien sur le disque** | base des comptes, table `favoris` |
| Note et case « Candidaté » | non | oui |
| Bandeau sur Explorer | « Tu as N favoris temporaires… Crée un compte pour les garder » | — |
| À la connexion / création du compte | les favoris temporaires sont **enregistrés automatiquement** (message « N favoris enregistrés dans ton compte ») | — |

**Comment ça marche.**
- `radar/accounts.py` : table `favoris` ; `add_favorite` (sans doublon : un réajout garde la note et la case), `remove_favorite`, `update_favorite` (note ≤ 500 caractères, case « candidaté »), `list_favorites`, `favorite_refs`. 500 favoris au plus ; supprimés avec le compte.
- `app/favoris.py` : même interface avec ou sans compte (`is_favorite`, `toggle`, `favorites`, `star_button`, `temp_banner`) ; `sync_offers_editor` applique les cases ★ cochées dans la liste des offres.
- `app/compte.py` : `_flush_temp_favorites`, appelée à la connexion et à la création du compte.
- Références : entreprise = SIRET ; offre = « source:offre_id ».

**Régler.** `FAVORITES_MAX_PER_USER`, `NOTE_MAX` (`radar/accounts.py`).

**Tests.** `uv run pytest -q tests/test_favoris.py` (étoile en anonyme sans écriture sur le disque, reprise à la connexion, étoile connectée, cases des offres) et `tests/test_accounts.py` (table `favoris`).

**Suites possibles.** Un vrai suivi de candidatures (statuts : à contacter, envoyée, relancée, réponse reçue) ; avec de vraies réponses, on pourrait un jour remplacer les réponses simulées du modèle (D6).

---

## 14. Entreprise et sites (T57)

**À quoi ça sert.** Une même entreprise apparaît sur plusieurs sites (Orange : 524 sites d'au moins 10 salariés). On veut voir **toute l'entreprise** et aussi **chaque site**, en sachant que c'est la même entreprise.

**Le principe.** Le **SIRET** (14 chiffres) identifie un **site** (établissement) ; le **SIREN** (9 chiffres, le début du SIRET) identifie l'**entreprise**. Tous les sites d'une entreprise ont le même SIREN. Limite : les filiales d'un groupe ont des SIREN différents et ne sont pas reliées (L24, T26).

**Ce que voit l'utilisateur.**

| Où | Ce qui change |
|---|---|
| **Fiche d'un site** | sous le nom : « Fait partie de ORANGE · 524 sites en France » + bouton **« Voir toute l'entreprise »** |
| **Fiche entreprise** (même fenêtre) | identité (catégorie, activité, nombre de sites, effectif total estimé, ville du siège), alerte BODACC, ☆ favori pour **toute l'entreprise**, **offres de tous ses sites**, **liste des sites** (les plus proches de ta ville d'abord ; clic → fiche du site), situation BODACC, lien Annuaire des entreprises (page entreprise) |
| **Navigation** | « ← Retour au site » depuis l'entreprise ; « ← Toute l'entreprise » depuis un autre site ouvert dans la liste |
| **Recherche (page Entreprises)** | d'abord une ligne **« ORANGE — toute l'entreprise · 524 sites en France »** par entreprise qui a plusieurs sites, puis les sites un par un ; clic → fiche entreprise ou fiche site |
| **Candidatures spontanées** | colonne **« Autres sites »** (« +4 » = 4 autres sites de la même entreprise dans le rayon) ; option **« Une ligne par entreprise »** dans « Filtres » (garde le site le mieux classé) ; la phrase de résultat donne les deux chiffres : « 3755 entreprises (4438 sites) » |
| **Favoris** | un site (comme avant) ou toute l'entreprise (référence « siren:… ») ; « Voir la fiche » rouvre la bonne fiche |

**Comment ça marche.**
- `radar/fiche.py` : `company_sites(siren, lat, lon)` (sites, triés par distance si une ville est choisie, sinon siège puis taille) et `company_summary(sites, siren)`.
- `radar/recherche.py` : `_n_sites` (nombre de sites par SIREN, calculé au chargement de l'index) et `with_companies(hits)` (lignes « entreprise » d'abord, colonne `_type`).
- `app/fiche_ui.py` : `open_fiche(siret, ligne, domaine, siren=None)` ; la fenêtre garde son état dans `st.session_state["_fiche_nav"]` (`origin`, `view`) pour passer du site à l'entreprise sans ouvrir de deuxième fenêtre ; `company_content(siren)`.
- `app/vues/explorer.py` : colonnes `_siren`, `_autres_sites` ; réglage `une_par_entreprise` (déclaré selon la consigne de `CLAUDE.md`).

**Tests.** `tests/test_fiche.py` (sites, résumé, navigation site ↔ entreprise dans la fenêtre) et `tests/test_recherche.py` (`with_companies`).

**Suites possibles.** Regrouper aussi les filiales d'un groupe (T26, par le nom) ; afficher les sites de l'entreprise sur une petite carte dans sa fiche.

