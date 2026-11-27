"""T21 — Rapprochement des offres sans SIRET (Adzuna) → complète data/processed/offres.parquet.

    uv run python scripts/classify_offres.py   # T13 (Emma), d'abord
    uv run python scripts/match_offres.py      # T21

Prérequis : data/processed/offres.parquet (T13) et data/processed/entreprises.parquet (T20).
"""

import logging

from radar.config import FILES, PATHS
from radar.process.offres import run


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    df = run()
    emp = df[~df["intermediaire"]]
    print(f"\n{len(df):,} offres → {FILES['offres'].relative_to(PATHS.root)}")
    print(f"  intermédiaires (sans SIRET, voulu) : {df['intermediaire'].mean():.1%}")
    print(f"  offres d'employeurs rapprochées    : {emp['siret_match'].notna().mean():.1%}")
    print(f"    dont confiance haute             : {emp['match_confiance'].eq('haute').mean():.1%}")
    print("  domaines :", df["domaine"].value_counts().to_dict())
    print("  contrats :", df["contrat"].value_counts().to_dict())


if __name__ == "__main__":
    main()
