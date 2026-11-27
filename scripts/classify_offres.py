"""T13 — Classe les offres brutes : data/raw/offres_raw/*.parquet → data/processed/offres.parquet

    uv run python scripts/classify_offres.py

Ajoute `domaine`, `contrat` (+ la règle qui a décidé) et le SIRET quand la source le donne
(La bonne alternance). Les offres Adzuna restent `match_methode = "a_rapprocher"` : le
rapprochement nom + commune est fait par T21. Affiche un résumé (dont les titres classés
« autre » les plus fréquents, utiles pour T8).
"""

from __future__ import annotations

import sys

from radar.config import FILES, PATHS
from radar.process.classify import RAW_DIR, classify_offers, load_raw_offers, summary


def main() -> int:
    raw = load_raw_offers()
    if raw.empty:
        print(f"Aucune offre brute dans {RAW_DIR.relative_to(PATHS.root)}/ : lancer un collecteur.")
        return 1
    offres = classify_offers(raw)
    offres.to_parquet(FILES["offres"], index=False)
    print(summary(offres))
    print(f"\n→ {FILES['offres'].relative_to(PATHS.root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
