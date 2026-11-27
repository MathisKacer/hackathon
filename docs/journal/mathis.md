# Journal — Mathis

---

## 2026-11-27 — Accès France Travail

**Fait :**
- `.env.example` créé ; jeton France Travail OK après souscription aux API.
- Scopes valides : La Bonne Boîte v2, ROME 4.0 Métiers, Marché du travail (non disponibles : Offres d'emploi, ROMEO, Fiches métiers).

**Résultats / chiffres clés :**
- La Bonne Boîte v2 renvoie le SIRET et un `hiring_potential` continu, mais elle couvre mal les métiers data fins (Rennes 30 km : 0 pour M1405 et M1419, 31 pour M1811). Limite de débit : erreur 429 à ~3 req/s.
- Liste des codes ROME 4.0 data dans `SOURCES.md`.

**Points d'attention pour l'équipe :**
- Copier `FT_SCOPES` depuis `.env.example`/`SOURCES.md` dans votre propre `.env`.

---

## 2026-11-27 — Modèle de réponse simulé

**Fait :**
- Décision D6 : modèle de réponse aux candidatures spontanées entraîné sur des réponses simulées (entreprises réelles), affiché comme démonstrateur. Tâches T35–T37.

---

## 2026-11-27 — Cadrage après le retour de l'équipe

**Fait :**
- Prise en compte : 24 h, équipe de 4 (Mathis, Celia, Maxence, Emma), France entière, domaine paramétrable, stage + alternance + emploi, LLM facultatif.
- `TACHES.md` réécrit en liste priorisée (P0 → P3) avec des jalons horaires, sans attribution ; décisions D3–D5 ; architecture et schémas mis à jour.

**Prochaine étape :**
- L'équipe pioche dans les P0 (accès aux API, squelette, données factices, dictionnaire des domaines).

---

## 2026-11-27 — T5 : pitch Radar + inventaire des sources

**Fait :**
- Pitch formalisé dans `docs/PROJET.md` ; architecture proposée et 4 rôles dans `ARCHITECTURE.md` / `TACHES.md`.
- Inventaire des sources dans `docs/SOURCES.md`, avec de vrais appels sur les API ouvertes.

**Résultats / chiffres clés :**
- ⚠️ L'API Offres d'emploi France Travail est **suspendue** (plus exposée sur francetravail.io).
- Recherche d'entreprises : `/near_point` fonctionne ; renvoie NAF, effectif, coordonnées et CA. Dans un rayon de 20 km autour de Rennes : 2 619 établissements en 62.01Z, 1 657 en 62.02A.
- Géocodage Géoplateforme et BODACC : fonctionnent sans clé.
- Ni Adzuna ni France Travail ne fournissent de SIRET → rapprochement nécessaire ; La bonne alternance en fournit.

**Prochaine étape :**
- Créer la clé Adzuna et le jeton La bonne alternance, puis mesurer le volume réel d'offres data dans le 35.

---

## 2026-11-27 — T0 : mise en place de la coordination

**Fait :**
- Création de `CLAUDE.md` (règles communes à toutes les sessions Claude).
- Création de `docs/` : `PROJET.md`, `ARCHITECTURE.md`, `TACHES.md`, `DECISIONS.md`, `journal/`.
- Ajout d'un `.gitignore` (données, secrets, environnements, caches).

**Fichiers touchés :**
- `CLAUDE.md`, `docs/*`, `.gitignore`, `README.md`

**Prochaine étape :**
- Pitch du projet → remplir `docs/PROJET.md` et découper en tâches dans `docs/TACHES.md`.
