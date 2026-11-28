# Journal — Emma

> Une entrée par session ou par tâche terminée, **la plus récente en haut**. Seule Emma écrit dans ce fichier.

---

## 2026-11-28 — T93 (essai, branche `emma/interface-riche`) : apparence plus marquée + tableau de bord

**Fait :**
- Choix d'Emma : mélange des pistes 4 (apparence) et 1 (tableau de bord). **Sur la branche seulement**, pas dans `main`.
- Apparence : `.streamlit/config.toml` (indigo, coins plus ronds, thèmes clair **et sombre** : menu ⋮ › Settings ; barre d'outils `viewer` pour que ce menu soit visible) ; `app/style.py` : CSS selon le thème actif (`st.context.theme.type`), bandeau dégradé indigo → turquoise avec un **radar animé** (SVG, points bleus et orange comme la carte) et des pastilles (« France entière », « Données ouvertes »…), tuiles avec icône, titres de section.
- **Logo « Compass »** (nom choisi par Emma, sur la branche seulement) : `app/static/compass_logo.svg` (clair), `compass_logo_sombre.svg`, `compass_icone.svg` (boussole au dégradé du bandeau, aiguille orange = candidatures spontanées) ; `st.logo` dans `app/streamlit_app.py` (version selon le thème), icône et titre de l'onglet « Compass ».
- Tableau de bord (`app/tableau_bord.py`, nouveau) sous les tuiles d'Explorer : 4 graphiques Altair (priorité, correspondance avec le CV, secteurs, tailles), barres fines, info-bulles, couleurs déjà utilisées dans la liste. Deux tuiles en plus : correspondance forte avec le CV, distance médiane.

**Fichiers touchés :**
- `.streamlit/config.toml`, `app/style.py`, `app/tableau_bord.py` (nouveau), `app/vues/explorer.py`, `docs/journal/emma.md`

**Résultats / chiffres clés :**
- Rennes, compétences Python/SQL/Statistiques : 4 graphiques affichés, pas d'erreur sur les 3 pages ; 384 tests passent. Pas de navigateur sur le pod : rendu à regarder par Emma.

**Problèmes / points d'attention pour l'équipe :**
- Touche l'apparence (@celia, D30, T70) : à montrer avant toute fusion.

**Prochaine étape :**
- Retours d'Emma sur le rendu ; éventuellement fiche plus détaillée (piste 3) ou cartes d'entreprises (piste 2).

---

## 2026-11-27 — T87 : correspondance plus visible ✅

**Fait :**
- Constat (Emma ne voyait pas la correspondance) : son profil ne contenait qu'une compétence non reconnue (« Célia »), donc aucune correspondance calculée, sans explication ; et la colonne était la dernière du tableau (13 colonnes).
- `NO_MATCH_MESSAGE` + colonne `correspondance_info` (Explorer) ; `match_summary` renvoie `{"info": …}` → message dans la liste (`st.info`), la fenêtre de la carte et la fiche.
- Colonne « Correspondance » insérée juste après « Priorité » ; dans la fenêtre de la carte, la ligne 🎯 est juste sous la priorité.

**Fichiers touchés :**
- `radar/competences.py`, `app/vues/explorer.py`, `app/carte.py`, `app/fiche_ui.py`, `tests/test_competences.py`, `docs/GUIDE.md`, `docs/TACHES.md`

**Résultats / chiffres clés :**
- Vraies données, Rennes : « Célia » → message dans la liste et la fenêtre ; « Python, SQL, Statistiques » → colonne après « Priorité », ligne 🎯 sous la priorité. Toute la suite passe.

**Problèmes / points d'attention pour l'équipe :**
- Rien ne s'affiche sans ville ni hors du domaine data (seul noté) : dit dans le GUIDE.
- Le serveur Streamlit du pod tournait depuis 23 h 13 : le relancer pour être sûr d'avoir la dernière version.

**Prochaine étape :**
- —

---

## 2026-11-27 — T86 : compétences une à une, sans bouton ✅

**Fait :**
- `app/cv_ui.py › profile_skills_editor(profile, save)` : boutons-étiquettes ✕ (un par compétence, dans un conteneur horizontal), champ « Ajouter une compétence » (`st.selectbox(..., accept_new_options=True)`, vidé après l'ajout), dépôt du CV ; chaque action enregistre aussitôt et met à jour la recherche en cours.
- `app/compte.py › _profile_section` : plus de bouton « Enregistrer » ; l'éditeur reçoit le profil et une fonction `save`. `app/vues/mon_espace.py` branche l'éditeur.
- Choix d'Emma : bouton retiré. Choix par défaut (non tranché) : la liste d'Explorer ne modifie pas le profil.
- D44, GUIDE § 4 et § 16, TACHES.

**Fichiers touchés :**
- `app/cv_ui.py`, `app/compte.py`, `app/vues/mon_espace.py`, `tests/test_compte_ui.py`, docs

**Résultats / chiffres clés :**
- Tests : ✕ retire du profil et de la recherche, l'ajout enregistre et vide le champ, pas de bouton « Enregistrer ». Vraie app (base temporaire) : Mon espace affiche Python, SQL, QGIS en étiquettes, sans erreur. Toute la suite passe.

**Problèmes / points d'attention pour l'équipe :**
- `app/compte.py` (@celia) : la signature de `profile_editor` change (`editor(profile, save)`), utilisée seulement par Mon espace.
- L'outil de test de Streamlit ne sait pas choisir une option tapée à la main : l'ajout libre passe par le même code, testé avec une option de la liste ; nettoyage testé à part.

**Prochaine étape :**
- Si tu veux : que la liste d'Explorer enregistre aussi dans le profil quand on est connecté.

---

## 2026-11-27 — T83 : compétences ajoutées à la main + CV depuis Mon espace ✅

**Fait :**
- `radar/competences.py` : `clean_skill(s)` (espaces, doublons casse/accents, 40 caractères, 60 compétences, libellé de la liste repris : « power bi » → « Power BI »), `custom_skills`, `match_skills` (« SQL Server » → SQL ; « QGIS » gardé mais ne compte pas dans la correspondance).
- `app/cv_ui.py` (nouveau) : `cv_and_skills(file_key)` = dépôt du CV + liste « Tes compétences » en saisie libre (`accept_new_options`), nettoyée avant chaque affichage. Utilisé par Explorer (Filtres › Ton CV) et par **Mon espace › Mes compétences** (demande d'Emma : y déposer aussi son CV).
- `app/compte.py` : `account_page(..., profile_editor=)` ; le bouton « Enregistrer mes compétences » apparaît dès que la liste diffère du profil (y compris pour tout retirer). `app/commun.py` : réglage `competences` en texte libre.
- D42, GUIDE § 4 et § 16, ARCHITECTURE, TACHES.

**Fichiers touchés :**
- `radar/competences.py`, `app/cv_ui.py` (nouveau), `app/compte.py`, `app/commun.py`, `app/vues/explorer.py`, `app/vues/mon_espace.py`, `tests/test_competences.py`, `tests/test_compte_ui.py`, docs

**Résultats / chiffres clés :**
- Vrai jeu de données, Rennes : compétences « Python, sql server, Stata » → gardées « Python, Sql server, Stata », correspondance calculée sur Python + SQL. Mon espace : CV, saisie libre et enregistrement testés (AppTest). Toute la suite passe.

**Problèmes / points d'attention pour l'équipe :**
- `app/compte.py` (@celia) : un paramètre facultatif de plus ; rien ne change sans lui.
- Une compétence tapée tout en minuscules prend une majuscule (« sql server » → « Sql server ») ; le reste est gardé tel quel.

**Prochaine étape :**
- T84 (recherches en favori), après ta réponse sur l'historique automatique.

---

## 2026-11-27 — T81 : profil = compétences du CV seulement ✅

**Fait :**
- Choix d'Emma : historique « Mes recherches » gardé tel quel ; compétences enregistrées avec un bouton.
- `app/commun.py` : `SAVED_PROFILE_KEYS = ("competences",)`, `saved_profile_keys()`. `app/compte.py` : `account_page(..., saved_keys=)` (création de compte et connexion avec les seules compétences), `_profile_section` (« Mes compétences » en étiquettes `:blue-badge[…]`, bouton « Enregistrer mes compétences » seulement si la recherche en cours en a d'autres), plus de bouton « Enregistrer mes réglages » ni de ligne « Profil enregistré : … ». `app/vues/mon_espace.py` passe `saved_keys`.
- D41 ; D14 annotée ; règle de CLAUDE.md mise à jour ; GUIDE § 4 ; SECURITE (données stockées).

**Fichiers touchés :**
- `app/commun.py`, `app/compte.py`, `app/vues/mon_espace.py`, `tests/test_compte_ui.py`, `CLAUDE.md`, docs (DECISIONS, GUIDE, SECURITE, TACHES)

**Résultats / chiffres clés :**
- Tests : profil affiché et enregistré avec les seules compétences ; connexion avec un ancien profil (contrat « Stage ») → seules les compétences reviennent. Toute la suite passe.

**Problèmes / points d'attention pour l'équipe :**
- **Change le travail de @celia (T48, D14)** et une règle de `CLAUDE.md` : décidé par Emma, à lui signaler. `compte.py` reste générique (sans `saved_keys`, tout est gardé : ses tests de T48 passent sans changement).
- `account_sidebar` (ancienne barre latérale, utilisée seulement par les tests) garde tous les réglages.

**Prochaine étape :**
- Proposer le domaine et le niveau d'études à partir du CV ; T46 (lettre).

---

## 2026-11-27 — T80 : correspondance CV ↔ entreprise, à part du score ✅

**Fait :**
- Demande d'Emma : les compétences ne comptent plus dans le score. Retrait de `c_adequation` de `COMPONENTS` / `DEFAULT_WEIGHTS` (`radar/spontaneous.py`) et de la raison correspondante (`radar/explain.py`) : score et classement identiques à avant T45 (vérifié à Rennes : mêmes premières entreprises avec ou sans compétences).
- `radar/competences.py` : `add_match` (colonnes `correspondance`, `correspondance_palier`, `correspondance_source`, `competences_demandees`, `competences_manquantes`), `match_tier`, `match_summary`, `MATCH_TIERS`, `MATCH_COLORS`. Choix d'Emma : paliers de mots, avec des seuils tels que « Forte » apparaisse.
- App : colonne « Correspondance » colorée (liste), ligne dans la fenêtre de la carte et dans la fiche (pourcentage, source, « Tu as », « Souvent demandé aussi »), tri « Correspondance » (`TRI_MATCH`, `app/commun.py`). D40 (D37 annotée).

**Fichiers touchés :**
- `radar/competences.py`, `radar/spontaneous.py`, `radar/explain.py`, `app/commun.py`, `app/vues/explorer.py`, `app/carte.py`, `app/fiche_ui.py`, `tests/test_competences.py`, docs (DECISIONS D40, LIMITES L29, GUIDE § 16, ARCHITECTURE, TACHES)

**Résultats / chiffres clés :**
- Seuils calés sur les vraies offres data : CV data complet (9 compétences) → médiane 17 %, 90e centile 29 % à Rennes comme à Paris. Rennes 20 km : 39 Forte, 100 Bonne, 291 Partielle, 70 Faible sur les 500 premières. CV « Excel, Power BI, SQL » : médiane 8 %, surtout Partielle / Faible.
- 373 tests passent.

**Problèmes / points d'attention pour l'équipe :**
- Code partagé modifié : `radar/spontaneous.py` (retour à la liste de composantes d'avant T45), `radar/explain.py`, `app/carte.py`, `app/fiche_ui.py` (une ligne en plus, à côté de la chance de réponse). Un ancien profil avec `poids_adequation` est simplement ignoré.
- `uv run ruff check .` signale des erreurs dans `notebooks/grille_llm_colab.ipynb` (@mathis, T77) et `ruff format .` le reformate : je ne l'ai pas touché (lint lancé sur `app radar tests scripts`).
- Seuls les scores data existent : pour les autres domaines la liste orange est vide, donc la correspondance n'a été mesurée que pour data.

**Prochaine étape :**
- T81 (profil = compétences seulement), après accord de @celia.

---

## 2026-11-27 — T45 : CV → compétences → adéquation ✅

**Fait :**
- `radar/competences.py` : liste fermée `SKILLS` (~85 compétences data, informatique, finance, marketing, RH, transversales) repérées par expressions (texte sans accents) ; choix prudents : pas « C » ni « Go », « R » seulement en majuscule isolée, « SAS au capital » écarté, « recrutement » de présentation (cabinets, forums) écarté. `pdf_text` (pypdf), `SkillProfile.build` (offres du domaine à ≥ 1 compétence, division NAF via `siret_match`), `add_adequation` (part des compétences de chaque offre que l'étudiant a, moyenne par secteur lissée vers le domaine, puis par entreprise ; `c_adequation` = rang dans la recherche ; `competences_demandees` pour l'explication). D37.
- App : Filtres › « Ton CV » (dépôt du PDF + multisélection « Tes compétences », réglage `competences` enregistré au profil selon la règle de CLAUDE.md ; le PDF n'est jamais écrit) ; nouveau curseur « Adéquation avec ton CV » ; explication de la carte et de la fiche.
- Choix d'Emma : option 1 (liste de compétences) et compétences gardées au profil.

**Fichiers touchés :**
- `radar/competences.py` (nouveau), `tests/test_competences.py` (nouveau), `radar/spontaneous.py`, `radar/explain.py`, `app/commun.py`, `app/vues/explorer.py`, `pyproject.toml`, `uv.lock` (pypdf), docs (DECISIONS D37, LIMITES L29, GUIDE § 16, ARCHITECTURE, TACHES)

**Résultats / chiffres clés :**
- Offres réelles : 51 % des offres data citent au moins une compétence (informatique 56 %, finance 70 %, marketing 66 %, RH 71 %) ; la moitié seulement est rattachée à un secteur. Profil construit en ~4 s (mis en cache).
- Rennes 20 km, stage, CV « Python, SQL, statistiques, Power BI, machine learning » : 9 des 20 premières entreprises inchangées (12 avec un poids de 1) ; montent INSERM, Météo-France, éditeurs de logiciels. Recalcul dans l'app ~7 s la première fois, puis rapide.
- 360 tests passent.

**Problèmes / points d'attention pour l'équipe :**
- **Code partagé modifié** (nécessaire à la tâche) : `radar/spontaneous.py` (`COMPONENTS`, `DEFAULT_WEIGHTS` + `c_adequation` ; `weighted_score` ignore maintenant une composante absente ou vide, comme un poids nul : sans effet sans CV, et la validation de @mathis, qui tire des poids au hasard, reste valable), `radar/explain.py` (une raison en plus). Nouvelle dépendance : `pypdf` → `uv sync`.
- Le dépôt du fichier n'est pas testable avec l'outil de test de Streamlit : la lecture du PDF est testée à part (PDF généré dans le test) et la liste des compétences dans l'app.
- Adéquation au niveau du secteur (L29) : à dire au pitch.

**Prochaine étape :**
- Possible : proposer le domaine et le niveau d'études à partir du CV ; T46 (lettre) pourrait réutiliser les compétences.

---

## 2026-11-27 — Note de passation : domaines par entreprise avec un LLM (T77, proposition)

**Fait :**
- Mise en note de toute la discussion sur « dans quels domaines une entreprise peut recruter » pour que @mathis reprenne : `docs/PISTE_DOMAINES_LLM.md` (objectif, sources testées et écartées, grille LLM NAF × taille × domaine, brouillon de consigne, précautions, moyens de calcul, branchement possible dans le score, étapes).
- T77 ajoutée dans TACHES (P2) comme **proposition à valider** ; BMO marquée testée dans SOURCES. Aucun code modifié, aucun LLM lancé.

**Fichiers touchés :**
- `docs/PISTE_DOMAINES_LLM.md` (nouveau), `docs/TACHES.md`, `docs/SOURCES.md`, `docs/journal/emma.md`

**Résultats / chiffres clés :**
- 718 NAF × 4 tailles × 5 domaines = 14 360 cases, une question par NAF (ou par 10) : ~72 appels, ~175 000 à 250 000 tokens.
- Temps : API ~10–20 min ; CPU open source ~3 h (pod sans GPU) ; GPU + vLLM quelques minutes (+ 20–40 min d'installation).

**Problèmes / points d'attention pour l'équipe :**
- Rouvre D21 (reportée) et touche `radar/score/build.py` (@mathis) : décision d'équipe nécessaire avant de coder.
- Pas de clé d'API remplie ni de GPU sur le pod d'Emma pour l'instant.

**Prochaine étape :**
- Décision d'équipe ; trouver un GPU (résultat de `nvidia-smi`) ou une clé ; préparer liste des NAF, consigne et script.

---

## 2026-11-27 — T74 : essai La Bonne Boîte pour la finance (domaines par entreprise)

**Fait :**
- Contexte : idée de donner à chaque entreprise un ou plusieurs domaines selon ce qu'elle peut recruter (reprise de D21, pas encore validée par l'équipe). Question testée : La Bonne Boîte peut-elle servir d'a priori par secteur **et** de signal propre à l'entreprise ?
- Avant : l'enquête BMO de France Travail (fichiers ouverts 2024 et 2026) a été écartée : métier × bassin d'emploi seulement, **pas de secteur**, et pas de métier « data » séparé.
- Collecte de la finance avec le collecteur existant (`radar/collect/lbb.py`, script temporaire hors dépôt), par paquets de 25 codes ROME (HTTP 500 au-delà). Résultat local : `data/raw/lbb_essai_finance.parquet` (pas dans Git, pas partagé). Aucun code du dépôt modifié.

**Fichiers touchés :**
- `docs/SOURCES.md`, `docs/TACHES.md`, `docs/journal/emma.md`

**Résultats / chiffres clés :**
- 20 611 établissements (M1203 comptabilité en tête), 70 % dans le référentiel, 3,5 % du référentiel signalé finance (data : 0,33 %) ; 157 signalés finance et data.
- Le NAF seul retrouve les signalés avec une **AUC de 0,97** (validation croisée par départements ; NAF × taille 0,97 ; taille seule 0,61 ; métiers des recruteurs LBA 0,66).
- Mais c'est un artefact : 247/315 gros NAF n'ont **aucun** signalé (gestion de fonds 0/636), et les secteurs en tête sont étonnants (jeux de hasard 75 %, grossistes en surgelés 58 %), banques 64.19Z 9 % seulement. La Bonne Boîte semble attribuer les métiers via une correspondance NAF ↔ ROME, puis classer par potentiel d'embauche global.

**Problèmes / points d'attention pour l'équipe :**
- **La Bonne Boîte ne dit pas « cette entreprise recrute en finance »** : le domaine vient du secteur. Même limite que les recruteurs LBA (L26). Pour la data (T28, D27), c'est déjà le cas : `c_embauche` reste valable comme **capacité d'embauche**, pas comme preuve d'un besoin data.
- Le seul signal propre à l'entreprise **par domaine** en données ouvertes reste ses **offres** (d'où l'intérêt de bien les classer : T68).

**Prochaine étape :**
- Décider avec l'équipe : a priori par secteur (La Bonne Boîte ou recruteurs LBA, présenté comme « d'après le secteur ») + offres classées (T68) pour le signal propre à l'entreprise.

---

## 2026-11-27 — T67 : niveau d'études attendu ✅

**Fait :**
- `radar/niveau.py` : niveaux du cadre européen comme LBA (« 3 » CAP … « 7 » Bac+5, « 8 » Doctorat). Champ `niveau_diplome` de LBA d'abord ; sinon expressions sur titre + description (Bac+N, Bac5, Master 1/2, M1/M2, MSc, Licence, Bachelor, BTS, DUT, école d'ingénieurs, Doctorat/PhD…), sans « Master Data », « Scrum Master », « BUT », « CAP », « ingénieur » seul. Plusieurs niveaux possibles (« 6,7 » → « Bac+3/4 à Bac+5 »). D34.
- App : filtre « Niveau d'études » (libellés, enregistrés dans le profil) + case « Garder les offres sans niveau précisé » (cochée par défaut) dans le panneau Filtres ; colonne « Niveau » dans l'onglet Offres ; 📚 niveau dans la fenêtre des offres de la carte ; colonne « Niveau » dans les offres de la fiche (`radar/fiche.py › company_offers`).
- Réglage ajouté selon la règle de CLAUDE.md (`WIDGET_KEYS`, `profile_keys()`, `PROFILE_LABELS`, `init_defaults()`).
- Docs : DECISIONS (D34), LIMITES (L27), GUIDE (section 15), ARCHITECTURE, TACHES (T67 fait, T71 ajoutée).

**Fichiers touchés :**
- `radar/niveau.py` (nouveau), `radar/fiche.py`, `app/commun.py`, `app/vues/explorer.py`, `app/carte.py`, `app/fiche_ui.py`, `tests/test_niveau.py` (nouveau), `tests/test_fiche.py`
- `docs/DECISIONS.md`, `docs/LIMITES.md`, `docs/GUIDE.md`, `docs/ARCHITECTURE.md`, `docs/TACHES.md`, `docs/journal/emma.md`

**Résultats / chiffres clés :**
- Vraie collecte Adzuna : **2,1 %** des offres avec un niveau détecté (221/10 776) — descriptions tronquées ; data : 18/42 alternances, 16/572 stages, 12/2 595 emplois. Surtout Bac+5.
- App testée (AppTest, vraies données) : Rennes 68 offres → « Bac+5 » seul : 0 ; avec les non précisées : 68. Paris : 1 483 → 1 482 → 25. Aucune exception liée à T67.
- `pytest` : 343/343 ; ruff OK.

**Problèmes / points d'attention pour l'équipe :**
- 🐞 **T71** : à Paris (20 km), la liste « Candidatures spontanées » plante (Styler pandas limité à 262 144 cellules, 575 560 ici) — code de T65, signalé, **non corrigé**.
- Fichiers d'autres tâches touchés (le minimum) : `app/vues/explorer.py`, `app/carte.py`, `app/fiche_ui.py`, `radar/fiche.py` (colonne/filtre « Niveau » seulement).
- Les vraies offres LBA ne sont pas sur mon pod (factices) : le taux de niveaux connus sur LBA réel reste à mesurer.

**Prochaine étape :**
- Mesurer la part de `niveau_diplome` renseignée sur les vraies offres LBA.

---

## 2026-11-27 — T19 : données factices alignées sur les vrais collecteurs ✅

**Fait :**
- Constat : le plantage décrit dans T19 (`region_requete` absente) n'existait plus — depuis la refonte en 3 pages, `app/commun.py › get_offers` déduit la région du code postal quand la colonne manque. Restait un écart de forme : les offres factices n'avaient que les 15 colonnes du contrat, pas celles propres à chaque source.
- `radar/fake_data.py` : `_source_columns` ajoute les colonnes d'Adzuna (`contrat_temps, categorie, salaire_min, salaire_max, salaire_predit, zone, requete, region_requete`) et de LBA (`partenaire, naf, naf_libelle, taille, adresse, niveau_diplome, nb_postes, statut, date_expiration, date_debut, duree_mois, teletravail, delegue_ecole`), dans l'ordre des collecteurs. Chaque fichier brut ne garde que ses colonnes ; `offres` (traitées) les a toutes, comme `classify_offres`.
- Formats vérifiés sur la vraie collecte Adzuna (libellés de catégories, « France > Région > … », 63 % sans salaire) et sur la spec OpenAPI publique de LBA (`niveau_diplome` ∈ « 3 »…« 7 », `teletravail` ∈ onsite/hybrid/remote, `statut` Active, tranches de taille LBA).
- Ces colonnes ont **leur propre générateur aléatoire** (`default_rng([seed, 19])`) : les autres tables factices sont identiques à graine égale (empreintes comparées avant/après).
- 4 tests dans `tests/test_fake_data.py`.

**Fichiers touchés :**
- `radar/fake_data.py`, `tests/test_fake_data.py`, `docs/TACHES.md`, `docs/ARCHITECTURE.md`, `docs/journal/emma.md`

**Résultats / chiffres clés :**
- Niveau d'études des offres LBA factices : surtout Bac+3/Bac+5 en data, ~10 % non renseigné. `pytest` : 309/309 ; ruff OK.

**Problèmes / points d'attention pour l'équipe :**
- Les vraies offres Adzuna n'ont **jamais de code postal** (100 % vide) alors que les factices en ont un : non modifié (le rapprochement factice en dépend), à garder en tête.
- `delegue_ecole` toujours faux dans les factices (le SIRET factice est celui de l'entreprise).
- `tests/test_compte_ui.py` (Celia) ajoute encore `region_requete="Bretagne"` aux offres factices : devenu inutile, laissé tel quel.
- Les données factices ne sont pas réécrites dans `data/` (vraies données sur mon pod) : relancer `make_fake_data.py` seulement sur un pod sans vraies données.
- `ruff format .` reformate aussi les blocs de code Python dans les `.md` (une ancienne entrée de ce journal).

**Prochaine étape :**
- T67 : niveau d'études attendu (LBA `niveau_diplome`, Adzuna à déduire du texte).

---

## 2026-11-27 — T34 : validation du score sans vérité terrain ✅

**Fait :**
- `radar/validation.py` : recalcul du score (intensité D13 + potentiel d'embauche D27) pour d'autres comptes d'offres, **identique à la production** (écart ≤ 3 × 10⁻⁸) ; métriques `overlap_at_k`, `auc`, `roc_points` ; analyses stabilité, poids, cohérence.
- `scripts/validate_scores.py` : lance les trois analyses sur le classement de la couche orange de l'app (`rank_spontaneous`, poids par défaut, top 20, 20 km, Rennes, Paris, Lyon, Toulouse, stage et alternance) → `data/processed/validation/` (JSON, CSV, 3 graphiques SVG générés sans dépendance).
- `docs/VALIDATION.md` : méthode, résultats, lecture et limites, rédigés pour le pitch. Graphiques copiés dans `docs/figures/` : ils ne contiennent que des chiffres agrégés, ni offres ni noms d'entreprises.
- `tests/test_validation.py` : 4 tests des métriques.
- Docs : `ARCHITECTURE.md`, commande dans `CLAUDE.md`, T34 en « Fait ».

**Fichiers touchés :**
- `radar/validation.py`, `scripts/validate_scores.py`, `tests/test_validation.py`, `docs/VALIDATION.md`, `docs/figures/validation_*.svg`
- `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/TACHES.md`, `docs/journal/emma.md`

**Résultats / chiffres clés :**
- **Stabilité** (50 tirages bootstrap) : 76 à 87 % du top 20 conservé selon la ville et le contrat (~80 % en moyenne).
- **Poids** : changer l'intensité ou le potentiel d'embauche garde 76 à 94 % du top 20 ; proximité, opportunité cachée et recruteur LBA changent vraiment la liste (voulu : préférences de l'étudiant). Poids tirés au hasard : 52 à 83 % conservé en moyenne.
- **Cohérence externe** (établissements **sans offre data**) : AUC de notre intensité **0,88** pour retrouver La Bonne Boîte et **0,81** pour La bonne alternance, contre **0,67** et **0,54** pour la taille seule.
- Relecture à la main du top 10 Rennes (stage) : ESN et conseil informatique, plausibles.
- `pytest` : 302/302 ; ruff OK.

**Problèmes / points d'attention pour l'équipe :**
- **Pour le pitch (T60)** : les 3 graphiques sont dans `docs/figures/`, et le texte prêt à reprendre est dans `docs/VALIDATION.md`.
- **Limite à assumer** : le haut de la liste est dominé par les ESN et le conseil (effet de l'a priori par secteur). Piste possible : un plafond par division NAF dans le top, ou un curseur « diversité ».
- Je voulais ajouter matplotlib au groupe dev pour les graphiques, mais le système de permissions a refusé la modification de `pyproject.toml` : les graphiques sont donc écrits en SVG à la main, sans nouvelle dépendance.
- Tension du marché (API Marché du travail) : non faite.
- **Push impossible depuis ma session** (identifiants VS Code périmés) : Emma doit synchroniser depuis VS Code.

---

## 2026-11-27 — T29 : La Bonne Boîte dans l'app ✅ (+ correction des dates factices)

**Fait :**
- T29 reprise à la place de @maxence, qui ne l'avait pas commencée (vérifié : ni commit ni branche).
- `radar/spontaneous.py` : curseur « Besoin attendu » renommé **« Potentiel d'embauche »**, explication corrigée (La Bonne Boîte d'abord, estimation sinon) ; nouvelle fonction `signaled_by_lbb(df)` et constante `LBB_SOURCE`.
- `app/streamlit_app.py` : colonne **« La Bonne Boîte » (✔)** dans la liste orange (affichée seulement s'il y a au moins un établissement signalé), ligne « ✔ Signalée par La Bonne Boîte (France Travail) (potentiel x) » dans la fenêtre de la carte (`_lbb_html`), légende du tableau mise à jour.
- **Bug trouvé et corrigé dans mon générateur factice (T5) :** il écrivait les dates en vraies dates, alors que les collecteurs réels les écrivent en texte ISO. Sur un pod qui mélange vraies offres Adzuna et `lba.parquet` factice (le mien), l'app plantait sur `offers['date_collecte'].max()` (`'>=' not supported between 'str' and 'Timestamp'`). Le générateur écrit maintenant du texte ISO (test ajouté). Sur mon pod, j'ai converti le seul `lba.parquet` factice, **sans relancer le générateur** (qui aurait écrasé les vraies offres Adzuna).
- Tests : `tests/test_lbb_display.py` (3) + 1 test de format de dates dans `tests/test_fake_data.py`.
- Docs : section 11 du `GUIDE.md`, T29 en « Fait ».

**Fichiers touchés :**
- `radar/spontaneous.py`, `app/streamlit_app.py`, `radar/fake_data.py`, `tests/test_lbb_display.py`, `tests/test_fake_data.py`
- `docs/GUIDE.md`, `docs/TACHES.md`, `docs/journal/emma.md`

**Vérifié :**
- `pytest` 273/273, ruff OK, après fusion avec le suggesteur de ville de Maxence (T55).
- App lancée (Streamlit AppTest, ville « Rennes ») : sans les colonnes La Bonne Boîte → aucune erreur, pas de colonne ✔ ; avec une copie des scores où 5 établissements rennais sont signalés → colonne présente, 5 ✔ sur 236, curseur « Potentiel d'embauche ».

**Problèmes / points d'attention pour l'équipe :**
- Les ✔ n'apparaîtront chez vous qu'après `collect_lbb.py` + `build_all.py` (@mathis) et le partage du nouveau `scores.parquet`.
- @celia : T38 (fiche entreprise) peut réutiliser `signaled_by_lbb` et `LBB_SOURCE` de `radar/spontaneous.py`.
- Si vous avez des données factices et réelles mélangées dans `data/raw/` : regénérez seulement ce qui est factice, jamais avec `--force` si de vraies offres sont présentes.

---

## 2026-11-27 — T28 : `c_embauche` réel avec La Bonne Boîte ✅

**Fait :**
- Exploration de l'API La Bonne Boîte v2. Champs utiles : `siret`, `rome`, `hiring_potential`, `naf`, position. Limites : `page_size` ≤ 100, `distance` ≤ 200 km. Découverte utile : on peut chercher **par région** et passer **plusieurs codes ROME dans une seule requête** (`rome` répété).
- `radar/collect/lbb.py` + `scripts/collect_lbb.py` : collecte des codes ROME data (non ambigus) de `domains.yaml`, région par région, avec pagination et cache disque (`data/cache/lbb_http`). NAF remis au format SIRENE (`62.02A`). Le drapeau `email` n'est pas conservé.
- `radar/score/embauche.py` : nouvelle règle de `c_embauche` (D27). Les établissements signalés par La Bonne Boîte passent devant, classés par `lbb_potentiel` ; les autres gardent l'ordre du proxy. Colonnes `c_embauche_source` et `lbb_potentiel`.
- `radar/score/build.py` (@mathis) : branchement minimal (paramètre `lbb` facultatif, lecture de `data/raw/lbb.parquet` s'il existe, sinon comportement d'avant avec un avertissement). `lbb_potentiel` ajouté au schéma `scores_reels`.
- `tests/test_embauche.py` : 6 tests sans réseau (ordre proxy conservé sans La Bonne Boîte, établissements listés devant, SIRET inconnus sans effet, format NAF, pagination, maximum sur les métiers).
- Docs : D27, L11 mise à jour, ligne La Bonne Boîte de `SOURCES.md` complétée, `ARCHITECTURE.md`, commande dans `CLAUDE.md`, T28 et T24 en « Fait ».

**Fichiers touchés :**
- `radar/collect/lbb.py`, `scripts/collect_lbb.py`, `radar/score/embauche.py`, `radar/score/build.py`, `radar/schemas.py`, `tests/test_embauche.py`
- `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/LIMITES.md`, `docs/SOURCES.md`, `docs/TACHES.md`, `docs/journal/emma.md`

**Résultats / chiffres clés :**
- Collecte : **30 appels**, **1 736 établissements** (M1811 Data engineer 1 433 ; M1403 139 ; C1105 64 ; H1215 40 ; C1120 22 ; M1419 16 ; M1405 13 ; M1889 9). Île-de-France 669, Auvergne-Rhône-Alpes 226, Bretagne 64. Aucun résultat pour statisticien, BI, Chief Data Officer, etc.
- Contrôle sur SIRENE (lecture à distance, sans rien écraser) : 100 % des SIRET connus, 99 % actifs, **77 % (1 331) dans notre référentiel** (actifs, ≥ 10 salariés). Les autres sont de petites structures. Ille-et-Vilaine : 33 dans le référentiel.
- `hiring_potential` médian 2,8 (0,6 à 86). `is_high_potential` vrai pour **un seul** établissement : inutilisable.
- `pytest` : 266/266 ; ruff OK.

**Problèmes / points d'attention pour l'équipe :**
- **@mathis :** sur ton pod (qui a la couverture Adzuna et les vraies données), lancer `uv run python scripts/collect_lbb.py` puis `uv run python scripts/build_all.py`, et repartager `scores.parquet`. Je n'ai pas pu recalculer les vrais scores sur mon pod : il me manque `adzuna_couverture.json`, `entreprises.parquet` réel et les vraies données LBA.
- Le modèle de réponse simulé (T36) utilise `c_embauche` : ses coefficients vont changer au prochain `build_all`.
- **@celia (fiche entreprise) / @maxence (app) :** `lbb_potentiel` et `c_embauche_source == "la_bonne_boite"` permettent d'afficher « signalée par La Bonne Boîte (France Travail) ». Tâches créées : **T29** (@maxence, libellé du curseur + badge) et **T38** (@celia, fiche).
- Limite restante (L11) : 99,7 % des établissements restent notés par le proxy. La Bonne Boîte couvre mal les métiers data pointus, c'est elle qui le dit, pas nous.

**Prochaine étape :**
- Selon les besoins de l'équipe (voir les tâches libres dans `TACHES.md`).

---

## 2026-11-27 — Décision d'équipe : focus sur les offres data

**Fait :**
- D21 (noter les domaines autres que data) passée en **« reportée »** : l'équipe ne s'intéresse qu'aux offres data pour le moment.
- T9 (nouvelles catégories de métiers) déplacée dans « Bloqué / en attente », marquée reportée.

**Fichiers touchés :**
- `docs/DECISIONS.md`, `docs/TACHES.md`, `docs/journal/emma.md`

**Points d'attention pour l'équipe :**
- L'app propose encore tous les domaines de `domains.yaml` (D20), mais seul data a un score : couche 🟠 vide pour les autres. **Décision : on laisse l'app telle quelle pour l'instant**, sans changer la liste des domaines.
- Répartition : **T51** (recruteurs LBA dans la couche 🟠) → @maxence ; **T28** (`c_embauche` réel) → @emma, après T51 (réservée dans `TACHES.md`). Les deux servent directement data et ne dépendent pas de D21.

---

## 2026-11-27 — T14 : test de l'API ROMEO ✅ (résultat : non retenue)

**Fait :**
- Scope trouvé : `api_romeov2` (jeton accepté ; `api_romeov1` et `romeo` refusés). Point d'accès : `POST /partenaire/romeo/v2/predictionMetiers`. Limites mesurées : **20 intitulés par appel**, **3 requêtes/s**.
- Test sur **200 vrais titres Adzuna distincts** (échantillon fixé par graine) : 50 anglais et 50 français classés `autre` par `classify`, plus 20 titres par domaine. Code ROME n°1 → domaine via `domains.yaml`, **relecture à la main** de tous les désaccords. Deuxième passe avec la description en contexte.
- Docs : D25 dans `DECISIONS.md`, ligne ROMEO de `SOURCES.md` complétée (technique + résultats), T14 en « Fait ».
- Rien dans le code : les scripts de test sont restés dans mon espace temporaire. Ils contiennent des titres d'offres Adzuna, qu'on ne redistribue pas.

**Fichiers touchés :**
- `docs/DECISIONS.md`, `docs/SOURCES.md`, `docs/TACHES.md`, `docs/journal/emma.md`

**Résultats / chiffres clés :**
- Sur les titres laissés en `autre` : ROMEO en place 27/100 dans un domaine, dont ~13 justes seulement.
- Sur les titres déjà classés : accord 51/100 ; sur les désaccords, mots-clés ~26 justes contre ROMEO ~10.
- Points faibles de ROMEO : titres RH anglais (« HR Generalist » → cadre de santé, « People Partner » → événementiel), titres data pourtant évidents (« Data Engineer - Aérospatial » → R&D industrie), titres commerciaux (« Account Executive - Acquisition » → fusions-acquisitions).
- Points forts : quelques vraies corrections des mots-clés (« Gestionnaire de paie… cabinet d'expertise comptable » → rh ; « Conducteur travaux CFO » → hors finance ; « Stage SEO… IA » → marketing).
- Le score de confiance ne permet pas de filtrer les erreurs. La description en contexte rend ROMEO instable (147/200 codes changés) sans l'améliorer.

**Problèmes / points d'attention pour l'équipe :**
- **ROMEO n'est pas branché.** Inutile d'ajouter `api_romeov2` à vos `.env`.
- Les quelques erreurs des mots-clés révélées par le test pourraient être corrigées dans `domains.yaml` (ex. exclure « expertise comptable » quand le titre parle de paie). Gain faible : à faire seulement dans T9 si quelqu'un y touche.

**Prochaine étape :**
- D21 attend toujours l'avis de Mathis et Maxence.

---

## 2026-11-27 — Proposition D21 : noter les domaines autres que data

**Fait :**
- Ajout de **T9** (nouvelles catégories de métiers) dans `TACHES.md`, puis correction : j'avais d'abord écrit qu'une collecte était nécessaire pour noter un domaine, alors que le calcul du score (`radar/score/build.py`) est générique. Seule la liste `SCORED_DOMAINS` le limite à data.
- Constat : depuis T41 (D20), l'app propose tous les domaines, mais la couche 🟠 est **vide** hors data, car `scores.parquet` ne contient que data.
- Rédaction de **D21, une proposition à valider** : La bonne alternance comme source pour tous les domaines (tous métiers, codes ROME, sans quota), Adzuna en complément avec la mention « signal partiel ».

**Fichiers touchés :**
- `docs/DECISIONS.md`, `docs/TACHES.md`, `docs/journal/emma.md`

**Problèmes / points d'attention pour l'équipe :**
- **@mathis, @maxence :** merci de valider ou modifier D21 avant que quelqu'un ne touche au score ou à l'app. Je n'ai modifié ni `radar/score/build.py` ni l'app.
- Pour vérifier les volumes par domaine, il faut les vraies données LBA sur S3 (T17) : mon pod n'a que des offres LBA factices.

**Prochaine étape :**
- Si D21 est validée : l'implémenter côté score (avec l'accord de Mathis), puis T9.

---

## 2026-11-27 — T8 : titres anglais mal classés ✅

**Fait :**
- Récupération des **vraies offres Adzuna** de Mathis (lien S3 privé, `curl`) : 10 776 offres dans `data/raw/offres_raw/adzuna.parquet` sur mon pod. `lba.parquet` est encore factice chez moi, donc seules les offres Adzuna ont été analysées.
- Mesure de la situation de départ, puis ajout de mots-clés anglais (et de quelques oublis) dans `radar/domains.yaml`, marqués `# T8`. J'ai vérifié **chaque bascule** de domaine sur les vraies offres, pas seulement les sorties de « autre ».
- Correction d'un bug : « Talent Acquisition » était classé marketing (mot-clé `acquisition` trop large).
- 27 tests de plus dans `tests/test_domains.py` (titres réels relevés, et pièges qui doivent rester « autre »).
- Docs : D17 dans `DECISIONS.md`, T8 en « Fait ».

**Fichiers touchés :**
- `radar/domains.yaml`, `tests/test_domains.py`
- `docs/DECISIONS.md`, `docs/TACHES.md`, `docs/journal/emma.md`

**Résultats / chiffres clés (10 776 offres Adzuna réelles, toutes issues de la recherche « data ») :**

| Domaine | Avant | Après |
|---|---|---|
| autre | 4 488 (41,6 %) | 3 939 (36,6 %) |
| data | 3 128 | 3 209 |
| informatique | 1 972 | 2 533 |
| finance | 616 | 549 |
| marketing | 416 | 371 |
| rh | 156 | 175 |

- Titres anglais classés « autre » : 941 → 746. Ceux qui restent sont surtout hors de nos 5 domaines (commerce, recherche clinique, « Project Manager » générique) : c'est voulu.
- Principales bascules : autre → informatique 462 (Business Analyst, architectes de solutions, Product Manager, consultants SAP, SRE…), autre → data 64 (Analytics Engineer, MLOps, Decision Scientist, Pricing Analyst, RWE), autre → finance 22 (Accountant, Capital Markets, Controlling), autre → rh 11 (People Partner, Recruitment), marketing → rh 13 (Talent Acquisition).
- Échantillon de 45 bascules autre → informatique relu à la main : aucune erreur.
- Rappel : 36,6 % de « autre » n'est pas un échec. La recherche Adzuna « data » ramène aussi des offres qui ne citent « data » que dans la description (ex. 142 « Négociateurs immobilier »).
- `pytest` : 190/190 ; ruff OK.

**Problèmes / points d'attention pour l'équipe :**
- **Pour @mathis :** relancer `uv run python scripts/build_all.py` pour que `offres.parquet` et les scores (T30/T31) prennent en compte les nouveaux classements, puis repartager les fichiers.
- Effet de bord assumé : 87 « Business Analyst Crédit/Assurance – Services financiers » passent de finance à informatique (au sens du ROME, ce sont des postes de consultant fonctionnel SI). À revoir si l'équipe préfère les laisser en finance.
- Erreurs connues restantes, rares : « Partnership Manager - Accountant Sector » → finance ; « Finaxys recrute un Project Management Office » → rh (le mot-clé `recrut` attrape le verbe « recrute » : 1 seule offre concernée sur les vraies données, je n'ai pas compliqué la règle pour ça).
- Pas encore vérifié sur les vraies offres La bonne alternance : il faut que Maxence les partage (T17). Elles ont des codes ROME, donc dépendent beaucoup moins des titres.

**Prochaine étape :**
- Selon les besoins de l'équipe : voir les tâches libres dans `TACHES.md`.

---

## 2026-11-27 — T7 : recruteurs La bonne alternance factices ✅

**Fait :**
- `radar/fake_data.py` › `make_recruteurs` : recruteurs potentiels factices au schéma `recruteurs_lba` de Maxence. Ils sont tirés **en dernier**, donc les autres tables restent identiques pour une même graine.
- `scripts/make_fake_data.py` écrit aussi `data/raw/lba_recruteurs.parquet`, au même endroit que le vrai collecteur, et refuse toujours d'écraser sans `--force`.
- 2 tests de plus dans `tests/test_fake_data.py` (schéma, SIRET valides, aucun recruteur avec une offre d'alternance, codes ROME connus, reproductibilité).
- Docs : T7 en « Fait », mention dans `ARCHITECTURE.md`.

**Fichiers touchés :**
- `radar/fake_data.py`, `scripts/make_fake_data.py`, `tests/test_fake_data.py`
- `docs/TACHES.md`, `docs/ARCHITECTURE.md`, `docs/journal/emma.md`

**Choix de réalisme :**
- Un recruteur potentiel est une entreprise **sans offre d'alternance publiée** : on les tire parmi les entreprises factices qui n'en ont pas (les plus grosses plus souvent), et jamais parmi celles en procédure collective.
- ~15 % de petites entreprises (tailles `0-0`, `1-2`, `3-5`, `6-9`) **absentes de `entreprises.parquet`**, comme dans le vrai export : ça permet de tester les jointures qui échouent.
- Tailles au format texte de La bonne alternance (`10-19`…), NAF au format `62.01Z` (comme SIRENE et LBA).
- `code_rome` : 1 à 4 **vrais** codes ROME 4.0 tirés de `domains.yaml` selon le secteur, donc les recruteurs data sont surtout dans l'informatique, le conseil et la finance. Les métiers hors des 5 domaines ne sont pas représentés, ce qui laisse `code_rome` vide pour ~25 % des recruteurs.
- Adresses en « rue Factice », URL en `example.org`, OPCO et IDCC tirés dans des listes réelles.

**Résultats / chiffres clés (graine 42) :**
- 662 recruteurs (85 % dans le référentiel), dont 154 avec un code ROME data et 44 à Rennes.
- Les autres tables sont inchangées (mêmes volumes qu'avant T7).
- `pytest` : 104/104 ; ruff OK.

**Problèmes / points d'attention pour l'équipe :**
- **Pour @maxence (couche orange de la carte) :** `make_fake_data.py --force` donne maintenant des recruteurs pour développer sans les 382 180 vrais. ⚠️ `--force` écrase aussi les fichiers d'offres : à ne pas lancer sur un pod qui a les vraies données.
- Vérification faite pendant T7 : la refonte de T21 par Mathis (`8dc3f96`) complète bien l'`offres.parquet` de T13 selon D10, et les SIRET d'école restent exclus. Rien à corriger.
- Sur mon pod, j'ai relancé `make_fake_data.py --force` : tout y était factice (vérifié avant d'écraser).

**Prochaine étape :**
- T8 (titres anglais) dès que Mathis partage les vraies offres.

---

## 2026-11-27 — T13 : classifieur d'offres ✅

**Fait :**
- `radar/process/classify.py` : `classify_offers(df)` ajoute aux offres brutes `domaine` (via `radar.domains.classify`), `contrat` (stage / alternance / emploi), la règle qui a décidé chacun (`domaine_regle`, `contrat_regle`) et le SIRET quand la source le donne. Les doublons (`source`, `offre_id`) sont supprimés. `summary()` fait un rapport texte.
- `scripts/classify_offres.py` : lit `data/raw/offres_raw/*.parquet`, écrit `data/processed/offres.parquet` et affiche le résumé, dont les titres classés « autre » les plus fréquents, qui serviront pour T8.
- `radar/domains.py` : nouvelle fonction `classify_with_rule` (domaine + règle) ; `classify` reste inchangée.
- `tests/test_classify.py` : 15 tests (règles de contrat, pièges comme « Médecin interne », doublons, SIRET d'école exclu, passage sur les offres factices).
- Docs : D10 dans `DECISIONS.md` (partage de `offres.parquet` entre T13 et T21), colonnes et valeurs de `match_methode` dans `ARCHITECTURE.md`, commande dans `CLAUDE.md`, T13 en « Fait ».

**Fichiers touchés :**
- `radar/process/classify.py`, `scripts/classify_offres.py`, `tests/test_classify.py`, `radar/domains.py`
- `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/TACHES.md`, `docs/journal/emma.md`

**Règles de contrat (la première qui s'applique) :**
1. Le contrat brut dit « Apprentissage » ou « Professionnalisation » (La bonne alternance) → alternance.
2. Le titre contient altern…, apprenti…, contrat pro, work-study → alternance.
3. Le titre contient stage, stagiaire, intern(ship), PFE, trainee → stage.
4. Sinon → emploi.

Le titre l'emporte sur le `contract_type` d'Adzuna (14 offres sur 50 seulement le renseignent, avec « permanent » ou « contract »). « Stage ou alternance » → alternance.

**Résultats / chiffres clés :**
- Sur les offres factices de mon pod (1 701) : tout passe, 100 % d'accord avec le domaine et le contrat factices. Ce n'est **pas** une mesure de qualité, puisque les titres factices sortent de mes propres listes ; ça montre seulement que la chaîne fonctionne. Je n'ai rien écrit dans `data/` (essai en mémoire).
- `pytest` : 94/94 sur tout le dépôt ; ruff OK.

**Problèmes / points d'attention pour l'équipe :**
- **Pour @mathis (T21) :** `offres.parquet` sort de T13 avec `match_methode = "a_rapprocher"` pour les offres Adzuna. T21 peut relire ce fichier et ne compléter que ces lignes (voir D10). Les offres La bonne alternance ont déjà leur SIRET (`siret_source`), sauf celles déléguées à une école (`siret_ecole_exclu`, SIRET retiré, 768 offres selon Maxence).
- **Pour @maxence (app) :** l'app pourra lire `domaine` et `contrat` dans `offres.parquet` au lieu d'utiliser `quick_filter.py`. Je n'ai pas touché à `quick_filter.py` ni à l'app.
- Sur mon pod, `data/raw/offres_raw/` contient encore les offres **factices** : il faut relancer `scripts/classify_offres.py` une fois les vraies offres récupérées (liens S3 de Mathis).
- Pour le domaine, seul le titre est utilisé, pas la description (tronquée à ~500 caractères chez Adzuna, risque de faux positifs). Piste possible plus tard, avec T8.

**Prochaine étape :**
- T7 (recruteurs LBA factices) : débloquée par la fusion de la branche de Maxence.
- T8 (titres anglais) dès que les vraies offres Adzuna sont partagées : `classify_offres.py` affiche déjà les titres « autre » les plus fréquents.

---

## 2026-11-27 — T6 : dictionnaire des domaines ✅

**Fait :**
- `radar/domains.yaml` : 5 domaines (data, informatique, finance, marketing, rh), chacun avec ses codes ROME 4.0 sûrs, ses codes ambigus, ses mots-clés et ses exclusions. La règle de classement est expliquée en tête du fichier.
- `radar/domains.py` : `load_domains()` (domaines dans l'ordre du fichier) et `classify(titre, code_rome)` → domaine ou `autre`. Gère plusieurs codes séparés par des virgules (format de La bonne alternance).
- `tests/test_domains.py` : 35 tests (fichier bien formé, un code ROME dans un seul domaine, mêmes domaines que le générateur factice, titres typiques et pièges).
- Docs : D9 dans `DECISIONS.md`, arborescence dans `ARCHITECTURE.md`, T6 en « Fait », T2 cochée (faite), nouvelle tâche T7 en attente.

**Fichiers touchés :**
- `radar/domains.yaml`, `radar/domains.py`, `tests/test_domains.py`
- `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/TACHES.md`, `docs/journal/emma.md`

**Comment j'ai obtenu les codes ROME :**
- Le fichier open data du ROME (francetravail.org) est **inaccessible depuis Onyxia** : la connexion est coupée.
- J'ai donc utilisé l'API France Travail « ROME 4.0 – Métiers », avec les clés du `.env` : `GET /partenaire/rome-metiers/v1/metiers/metier?champs=code,libelle,domaineProfessionnel(code,libelle,grandDomaine(code,libelle)),appellations(libelle)`, soit 1 923 métiers.
- J'ai choisi les codes à la main, à partir des domaines professionnels (M14 études, M18 SI, M12 comptabilité-gestion, C12/C13 banque-finance, M17/E11/E14 marketing-communication, M15 RH) et d'une recherche de mots-clés dans les appellations. Les libellés du YAML sont recopiés depuis l'API.
- Le script d'extraction n'est pas versionné : c'était un usage ponctuel, et c'est le YAML qui fait foi.

**Résultats / chiffres clés :**
- Nombre de codes sûrs (+ ambigus) : data 18 (+ 8 ambigus), informatique 82, finance 49, marketing 34, rh 11.
- Codes data ajoutés à la liste de `SOURCES.md` : M1422 (directeur d'études socio-éco), M1873 (IA embarquée), K2134 (démographe), H1215 (bio-informaticien). M1824 (BI) est confirmé.
- Codes ambigus data : M1430 (études commerciales), M1435 (tracking), M1201 (analyste financier, quant), M1853 (chef de projet informatique, « projet Data »), M1894 (gestionnaire de bases de données), M1895 (géomaticien), M1888 (modélisation climatique), G1211 (analyste de la performance sportive).
- Les mots-clés data reprennent ceux de `quick_filter.py` (Mathis, T39), avec le même verdict sur ses 18 titres de test. J'ai ajouté des exclusions : datacenter, DPO / protection des données, saisie de données.
- `pytest` : 69/69 sur tout le dépôt ; ruff OK.

**Problèmes / points d'attention pour l'équipe :**
- **Pas encore validé sur de vraies offres** : les données Adzuna de Mathis sont sur son pod, et je n'ai pas relancé de collecte pour ne pas consommer le quota partagé. Pour comparer sur les vraies offres :
  `uv run python -c "import pandas as pd; from radar.domains import classify; df=pd.read_parquet('data/raw/offres_raw/adzuna.parquet'); print(df['titre'].map(classify).value_counts())"`
- Les titres anglais hors data sont mal couverts (« Accounting Generalist » → `autre`) : à compléter dans T13 si besoin.
- Un code sûr l'emporte sur le titre : « Data engineer » avec un code M1805 (développeur) → informatique. C'est voulu, le ROME étant plus fiable que le titre.
- `quick_filter.py` (T39) reste en place : je n'y ai pas touché. T13 pourra le remplacer par `classify`.
- `fake_data.DOMAINS` doit rester identique aux clés du YAML : un test le vérifie.

**Prochaine étape :**
- T7 (recruteurs LBA factices), **seulement après la fusion de la branche de Maxence** (T11), pour ne pas toucher `schemas.py` en même temps que lui.
- Formats à harmoniser avec Maxence (vus dans sa branche) : NAF `6201Z` (La bonne alternance) contre `62.01Z` (SIRENE et données factices), et taille en fourchette (`50-99`) contre codes INSEE de tranche d'effectif.

---

## 2026-11-27 — T5 : générateur de données factices ✅

**Fait :**
- `radar/fake_data.py` : génère, de façon reproductible (graine), **tous** les fichiers du contrat de `ARCHITECTURE.md` avec des entreprises inventées.
- `scripts/make_fake_data.py` : écrit les fichiers dans `data/`. Il refuse d'écraser des fichiers existants (de vraies données, peut-être) sans `--force`.
- `radar/schemas.py` : colonnes du contrat en code + `check_columns()`, utilisables par tout le monde (décision D7).
- `tests/test_fake_data.py` : 5 tests (schémas, SIRET valides, liens offres ↔ entreprises, une ligne par (siret, domaine), reproductibilité).
- Docs : D7 dans `DECISIONS.md` ; arborescence et emplacement des offres brutes dans `ARCHITECTURE.md` (j'ai aussi supprimé la ligne vide qui coupait le tableau des schémas) ; commande ajoutée dans `CLAUDE.md` › Stack ; T5 passée en « Fait ».

**Fichiers touchés :**
- `radar/fake_data.py`, `radar/schemas.py`, `scripts/make_fake_data.py`, `tests/test_fake_data.py`
- `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/TACHES.md`, `docs/journal/emma.md`

**Comment l'utiliser :**
```bash
uv run python scripts/make_fake_data.py          # 3 000 entreprises, graine 42 (≈ 6 s)
uv run python scripts/make_fake_data.py -n 10000 --seed 1 --force
```
```python
from radar.fake_data import generate  # tout en mémoire, sans écrire de fichier

data = generate(n_entreprises=500, seed=0)  # data.entreprises, data.offres, data.scores…
```

**Résultats / chiffres clés (graine 42, 3 000 entreprises) :**
- 3 000 entreprises de ≥ 10 salariés autour de 24 villes (Paris 960, Lyon 261, Rennes 251…), dans 21 secteurs NAF ; SIRET et SIREN valides (clé de Luhn).
- 1 701 offres (1 514 Adzuna, 187 La bonne alternance) ; 23 % des entreprises ont au moins une offre (loi gamma-Poisson : beaucoup de zéros) ; 17 % des offres sont « data » ; 68 % emploi, 17 % stage, 15 % alternance.
- 80 % des offres Adzuna sont rapprochées d'un SIRET (méthode `nom_commune_fuzzy`) ; les offres La bonne alternance ont leur SIRET (`siret_source`).
- Domaine data : 180 entreprises recrutent dans la data, dont **142 sans offre de stage data** → des « opportunités cachées » à montrer dans l'app.
- `scores.parquet` : 15 000 lignes (3 000 × 5 domaines) ; `candidatures_simulees` : 3 000 lignes (taux de réponse 25 %) ; `p_reponse` : 30 000 lignes.
- Vérifié : `pytest` 7/7, ruff OK, l'app Streamlit charge les 3 000 entreprises sans erreur.

**Problèmes / points d'attention pour l'équipe :**
- ⚠️ **Tout est factice** : ne jamais montrer ces chiffres comme réels. Les descriptions portent `[DONNÉE FACTICE]` et les URL pointent vers `example.org`.
- Les formules de `scores`, `candidatures_simulees` et `p_reponse` sont **provisoires**, faites seulement pour avoir les bonnes colonnes : T30/T31 et T35/T36 (pas encore attribuées) les remplaceront.
- Domaines provisoires (`data, informatique, finance, marketing, rh` + `autre`) en attendant `domains.yaml` (T6). Codes ROME renseignés pour les offres data seulement (les codes de `SOURCES.md`) ; les autres domaines restent vides plutôt que d'inventer des codes.
- `data/` n'est pas dans Git : chacun lance le script sur son pod. T12 (@mathis) écrit aussi `data/raw/offres_raw/adzuna.parquet` : si son collecteur tourne sur un pod où le fichier factice existe déjà, il l'écrasera (c'est voulu). Dans l'autre sens, mon script refuse d'écraser ses vraies données.
- Colonnes en plus du contrat (permises) : `p_reponse.contrib_intensite`, `p_reponse.contrib_taille`, et `c_intensite` + `log_taille` dans `candidatures_simulees` (ce sont les `<variables>` du schéma).
- Relecture des docs (avant T5) : incohérences repérées et **non corrigées**, à trancher en équipe. Le passage de l'intensité « part des offres » (bêta-binomial) à « offres / effectif » (gamma-Poisson) après le test Adzuna n'est pas encore répercuté dans `PROJET.md`, `ARCHITECTURE.md` (modèle de score), ni dans l'ordre T31/T33. La colonne `lbb_proba` contient en réalité `hiring_potential` (un score, pas une probabilité). Le schéma de `ARCHITECTURE.md` parle encore de collecte « quotidienne » et de `scores_composantes.parquet`. D2 et `SOURCES.md` parlent encore de la Bretagne seule.

**Prochaine étape :**
- Proposer à l'équipe les corrections de docs ci-dessus, puis prendre T40 (page de recherche) ou T30 (score v0), qui sont débloquées par T5.

---

