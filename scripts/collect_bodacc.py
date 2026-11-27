"""Procédures collectives BODACC → colonnes procedure_* de entreprises.parquet (T23, D23).

    uv run python scripts/collect_bodacc.py            # utilise le cache s'il existe
    uv run python scripts/collect_bodacc.py --refresh  # retélécharge les annonces (~1 min)

Prérequis : data/processed/entreprises.parquet (scripts/extract_sirene.py).
Aussi lancé par scripts/build_all.py, juste après l'extraction SIRENE.
"""

import argparse
import logging

from radar.collect.bodacc import run


def main() -> None:
    p = argparse.ArgumentParser(description="Procédures collectives BODACC (T23)")
    p.add_argument("--refresh", action="store_true", help="retélécharger les annonces BODACC")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run(refresh=args.refresh)


if __name__ == "__main__":
    main()
