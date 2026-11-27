"""T28 — Collecte La Bonne Boîte v2 → data/raw/lbb.parquet

    uv run python scripts/collect_lbb.py              # domaine data (~30 appels, < 1 min)

Prérequis : FT_CLIENT_ID / FT_CLIENT_SECRET / FT_TOKEN_URL dans .env (scope La Bonne Boîte
souscrit). Les réponses sont en cache dans data/cache/lbb_http.sqlite : relancer ne refait pas
les appels. Ensuite : `uv run python scripts/build_all.py` pour recalculer `c_embauche`.
"""

import argparse
import logging

from radar.collect.lbb import OUT_FILE, collect
from radar.config import PATHS


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--domaine", default="data")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    df = collect(args.domaine)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_FILE, index=False)
    print(f"\n{len(df):,} lignes (établissement × métier) → {OUT_FILE.relative_to(PATHS.root)}")
    print(f"  établissements distincts : {df['siret'].nunique():,}")
    print(f"  fort potentiel           : {df.groupby('siret')['lbb_fort_potentiel'].any().sum():,}")
    print("  par métier :", df["rome"].value_counts().to_dict())


if __name__ == "__main__":
    main()
