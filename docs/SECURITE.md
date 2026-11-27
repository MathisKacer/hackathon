# Sécurité des comptes et des mots de passe

> Ce que Radar fait pour protéger les comptes (T48, T49), pourquoi, et ce qui manque. Décisions : **D14** (comptes facultatifs) et **D16** (règles et blocage). Code : `radar/accounts.py` (règles, hachage, blocage) et `app/compte.py` (formulaires). Tests : `tests/test_accounts.py`, `tests/test_compte_ui.py`.
> Mettre à jour ce fichier à chaque changement touchant aux comptes.

## En bref (pour le pitch)

- **Pas de compte obligatoire** : la démo marche en anonyme, sans rien enregistrer.
- **Mots de passe jamais stockés en clair** : hachés avec **scrypt** et un sel par compte.
- **Règles inspirées de la CNIL** : au moins 12 caractères et 3 types de caractères ; mots de passe courants refusés.
- **Blocage après 5 échecs** : compte bloqué 15 minutes, même en rechargeant la page.
- **Minimum de données personnelles** : pas d'e-mail, et « Supprimer mon compte » efface tout (profil, favoris, recherches).
- **Administrateurs = l'équipe seulement** (T79, D39) : nommés uniquement en ligne de commande sur le serveur, jamais depuis le site ; ils voient des nombres, pas le contenu des comptes ; chaque action est journalisée.

## Choix du mot de passe (à la création du compte)

| Règle | Valeur | Pourquoi |
|---|---|---|
| Longueur | **12 à 128 caractères** | La longueur est ce qui rend un mot de passe difficile à deviner (CNIL : 12 minimum avec plusieurs types de caractères) |
| Diversité | **au moins 3 types** parmi minuscules, majuscules, chiffres, caractères spéciaux (l'espace compte comme spécial) | Version simplifiée de la recommandation CNIL ; laisse passer les phrases de passe (« velo rouge 2026 Rennes ») |
| Mots de passe courants | **refusés** (liste de ~35 mots de passe très répandus : `Motdepasse123`, `AZERTY123456`…), sans tenir compte de la casse | Ce sont les premiers essayés par un attaquant |
| Identifiant | **interdit dans le mot de passe** (`Celia-2026!` refusé pour l'identifiant `celia`) | Trop facile à deviner |
| Message d'erreur | liste exactement les règles non respectées | L'utilisateur sait quoi corriger |

Les règles sont affichées sous le champ « Mot de passe » du formulaire de création. Pour les changer : constantes `PASSWORD_*` et `COMMON_PASSWORDS` dans `radar/accounts.py` (le texte d'aide `PASSWORD_RULES` suit).

## Stockage

- **Hachage scrypt** (`hashlib.scrypt`, bibliothèque standard de Python ; paramètres n = 2¹⁴, r = 8, p = 1, soit ~50 ms et 16 Mo par vérification) : coûteux à attaquer par force brute, même si la base fuit.
- **Sel aléatoire de 16 octets par compte** : deux mots de passe identiques donnent deux empreintes différentes, et les tables précalculées sont inutiles.
- **Format stocké** : `scrypt$n$r$p$sel$empreinte`. Les paramètres sont dans l'empreinte : on peut les durcir plus tard sans casser les comptes existants.
- **Comparaison à temps constant** (`hmac.compare_digest`).
- **Base** : `data/app/radar.db` (SQLite), **jamais dans Git ni sur S3**. Le mot de passe en clair n'est ni stocké, ni journalisé, ni affiché.

## Où est la base ? (hébergement)

Il n'y a **pas de serveur de base de données** : on utilise **SQLite**, une base qui tient entièrement dans **un fichier**, `data/app/radar.db`. L'app Streamlit ouvre ce fichier et y écrit directement, comme on écrirait dans un fichier Excel.

```
Navigateur ──(internet, proxy Onyxia …/proxy/8501/)──► service VS Code Onyxia (SSP Cloud)
                                                       ├─ app Streamlit (Python)
                                                       │     └─ lit / écrit ─► data/app/radar.db
                                                       └─ /home/onyxia/work = disque persistant
                                                          (datacenter du SSP Cloud, rattaché au service)
```

| Action | La base… |
|---|---|
| Arrêter / relancer l'app Streamlit | est conservée |
| Mettre en pause / relancer le service VS Code | est conservée (disque persistant) |
| `git pull` / `git push` | n'est pas touchée (hors Git) |
| **Supprimer le service** sur Onyxia | **est perdue** (avec tout le dossier `work`) |
| Ouvrir l'app depuis le pod d'un coéquipier | **c'est une autre base** : chaque pod a la sienne |

Conséquence pour la démo : créer les comptes de démonstration **sur le pod qui sert à la présentation**. Comparaison : aujourd'hui, c'est un fichier Excel sur un ordinateur ; une base hébergée (Supabase, PostgreSQL) serait l'équivalent d'un Google Sheets partagé et sauvegardé (tâche T52, très optionnelle).

## Connexion

- **Blocage par compte, enregistré en base** : après **5 échecs d'affilée**, le compte est bloqué **15 minutes**. Pendant le blocage, même le bon mot de passe est refusé. Une connexion réussie remet le compteur à zéro. Recharger la page ou ouvrir un autre onglet ne contourne pas le blocage. Réglages : `LOGIN_MAX_FAILS`, `LOGIN_LOCK_DURATION`.
- **Identifiant inconnu** : on vérifie quand même un haché factice, pour que le temps de réponse ne révèle pas si le compte existe. Le message est le même : « Identifiant ou mot de passe incorrect ».
- **Identifiants** normalisés (minuscules, espaces retirés) : `Celia` et `celia` sont le même compte.

## Administrateurs et gestion des comptes (T79, D39)

- **Qui** : les membres de l'équipe seulement, **4 au plus** (`MAX_ADMINS`). On devient administrateur **uniquement** par `uv run python scripts/admin.py promouvoir <identifiant>` dans le terminal du pod (accès réservé à l'équipe). Aucun bouton du site ne permet de nommer un administrateur, et aucun identifiant n'est écrit dans le code : sinon le premier venu qui crée le compte « maxence » deviendrait administrateur.
- **Ce qu'ils font** (page « Administration », visible seulement par eux et revérifiée à chaque affichage) : voir la liste des comptes, **débloquer** un compte, donner un **mot de passe provisoire** (généré aléatoirement, conforme aux règles, affiché une seule fois, à transmettre par un moyen privé ; l'utilisateur est invité à le changer), **supprimer** un compte classique.
- **Limites** : un administrateur ne réinitialise ni ne supprime le compte d'un autre administrateur (ça se règle entre membres, par le script) ; il ne peut pas se supprimer depuis la page (passer par Mon espace).
- **Vie privée** : la liste montre des **nombres** (recherches, favoris, profil oui/non), jamais leur contenu.
- **Journal** (`admin_log`) : date, auteur (ou « (terminal) » pour le script), action, compte visé.
- **Pour tout le monde** : « Changer mon mot de passe » dans Mon espace (ancien mot de passe vérifié, mêmes règles qu'à la création).
- Code : `radar/admin.py`, `app/admin_ui.py`, `app/vues/administration.py`, `scripts/admin.py` ; tests : `tests/test_admin.py`.

## Données personnelles

- Données stockées : identifiant, empreinte du mot de passe, profil (compétences tirées du CV seulement, D41 ; le CV n'est jamais conservé), favoris, et recherches **enregistrées à la demande** (20 max, réglages seulement dont la ville ; ni entreprises ni résultats, T84). Une base créée avant T84 peut encore contenir l'ancien historique automatique (table `recherches`, plus alimentée ni affichée). **Pas d'e-mail, pas de nom.**
- « Supprimer mon compte » efface le compte, le profil, les favoris et les recherches (suppression en cascade).
- En mode anonyme, rien n'est écrit sur le disque.

## Ce qui manque (assumé pour un hackathon de 24 h)

| Manque | Risque | Ce qu'il faudrait en production |
|---|---|---|
| Base locale au service Onyxia (L17) | Comptes perdus si le service est supprimé ; un compte n'existe que sur le pod où il a été créé ; pas de sauvegarde | Base hébergée avec sauvegardes (Supabase : tâche T52, très optionnelle) |
| Pas de « mot de passe oublié » automatique (L18) | Atténué (T79) : un administrateur peut donner un mot de passe provisoire, à transmettre hors de l'app | Récupération par e-mail (donc collecter un e-mail) |
| Pas de « se souvenir de moi » (L18) | Recharger la page déconnecte | Cookie de session signé, avec expiration |
| Le message de blocage révèle qu'un compte existe (L19) | Un attaquant peut tester si un identifiant existe en provoquant un blocage | Bloquer aussi les identifiants inconnus, ou limiter par adresse IP |
| Pas de vérification contre les fuites connues (L19) | Un mot de passe déjà fuité mais « conforme » passe | Service *Have I Been Pwned* (k-anonymat) ou grande liste locale |
| Pas de double authentification | Un mot de passe volé suffit | TOTP (application d'authentification) |
| HTTPS | Fourni par le proxy Onyxia (`…/proxy/8501/`) | À garantir sur tout autre hébergement |

## Références

- CNIL, recommandation relative aux mots de passe (délibération n° 2022-100 du 21 juillet 2022).
- NIST SP 800-63B (*Digital Identity Guidelines*) : longueur plutôt que complexité, refus des mots de passe compromis, limitation des tentatives.
