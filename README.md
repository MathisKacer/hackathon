# Radar

Projet de hackathon — ENSAI, M2. Trouver les entreprises qui ont besoin de ton profil, même sans offre publiée.

- Le projet : [`docs/PROJET.md`](docs/PROJET.md)
- L'architecture : [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Qui fait quoi : [`docs/TACHES.md`](docs/TACHES.md)
- Règles de travail (humains et Claude) : [`CLAUDE.md`](CLAUDE.md)

## Démarrage (une seule fois)

Fonctionne sur Onyxia, Linux, macOS et Windows.

1. Installer **uv** : <https://docs.astral.sh/uv/getting-started/installation/> (déjà présent sur Onyxia).
2. Cloner le dépôt puis installer l'environnement :
   ```bash
   git clone https://github.com/MathisKacer/hackathon.git
   cd hackathon
   uv sync
   ```
3. Clés d'API (seulement si tu lances des collecteurs ; l'app n'en a pas besoin) :
   ```bash
   cp .env.example .env    # puis remplir ; clés transmises en message privé
   ```

## Récupérer les données

Les données ne sont **pas** dans Git (dépôt public). Mathis les partage depuis Onyxia avec des liens
temporaires (valables 24 h) envoyés en **message privé**, sous forme d'une commande `curl` :

```bash
# depuis la racine du dépôt (le dossier hackathon/)
curl --create-dirs -o data/raw/offres_raw/adzuna.parquet "https://minio.lab.sspcloud.fr/…"
```

- **Windows (PowerShell)** : écrire `curl.exe` au lieu de `curl`, le reste est identique.
- Lien expiré (erreur 403 ou fichier de quelques octets) → demander un nouveau lien à Mathis.
- Ne jamais partager publiquement ces liens ni ces fichiers.

## Lancer l'application

```bash
uv run streamlit run app/streamlit_app.py
```

Puis ouvrir <http://localhost:8501> (sur Onyxia : `<URL de ton service>/proxy/8501/`).
