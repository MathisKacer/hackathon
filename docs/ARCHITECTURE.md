# Architecture

> Le « comment ». Mettre à jour dès qu'un dossier, un module ou un format de données est ajouté ou modifié.

## Vue d'ensemble

_TBD — schéma du pipeline une fois le projet défini, par ex. :_

```
données brutes → nettoyage → features → modèle → résultats → app / slides
```

## Arborescence du dépôt

```
hackathon/
├── CLAUDE.md            # Règles communes pour toutes les sessions Claude
├── README.md
├── docs/
│   ├── PROJET.md        # Pitch, objectifs, livrables
│   ├── ARCHITECTURE.md  # Ce fichier
│   ├── TACHES.md        # Tableau des tâches
│   ├── DECISIONS.md     # Journal des décisions
│   └── journal/         # Un journal d'avancées par personne
├── data/                # Données locales (ignoré par Git)
└── …                    # À compléter (src/, notebooks/, app/…)
```

## Modules

| Module / dossier | Responsabilité | Entrées | Sorties | Responsable |
|---|---|---|---|---|
| _TBD_ | | | | |

## Données et formats intermédiaires

Décrire ici chaque fichier intermédiaire partagé entre modules (chemin, format, colonnes clés) — c'est le **contrat** entre coéquipiers.

| Fichier | Produit par | Utilisé par | Format / colonnes |
|---|---|---|---|
| _TBD_ | | | |

## Stack technique

- Langage : _TBD_
- Librairies principales : _TBD_
- Environnement : Onyxia / SSP Cloud
- Stockage données : _TBD (local `data/` ou S3)_

## Conventions

- Langue du code (noms de variables, fonctions) : _TBD_
- Style / formatage : _TBD (ex. ruff/black, styler)_
- Chemins : relatifs à la racine du dépôt, jamais de chemins absolus personnels.
