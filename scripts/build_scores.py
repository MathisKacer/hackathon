"""Score v0 (T30/T31) → data/processed/scores.parquet

    uv run python scripts/build_scores.py

Prérequis (ordre du pipeline) : extract_sirene.py → classify_offres.py → match_offres.py.
"""

import logging

from radar.config import FILES, PATHS
from radar.score.build import load_coverage, run


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    s = run()
    print(f"\n{len(s):,} lignes (siret × domaine) → {FILES['scores'].relative_to(PATHS.root)}")
    print(
        "Couverture de la collecte par région :",
        {k: round(v, 2) for k, v in load_coverage().items()},
    )
    comp = s.drop_duplicates("siren")
    covered = (comp["couverture"] > 0).mean()
    print(f"Entreprises notées : {len(comp):,} ; dans une zone couverte : {covered:.1%}")
    print(f"Entreprises avec ≥ 1 offre du domaine : {(comp['n_offres_domaine_siren'] > 0).sum():,}")
    print("\nA priori par division NAF (offres data / 100 salariés), les plus élevés :")
    pri = comp.groupby(["naf_division"])["prior_moyenne"].first().sort_values(ascending=False)
    print(pri.head(8).round(4).to_string())


if __name__ == "__main__":
    main()
