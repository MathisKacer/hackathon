"""T5 — Écrit les données FACTICES dans data/ pour démarrer le score et l'app sans la collecte.

    uv run python scripts/make_fake_data.py              # 3 000 entreprises, graine 42
    uv run python scripts/make_fake_data.py -n 10000 --seed 1 --force

Fichiers produits (contrat de docs/ARCHITECTURE.md) :
    data/raw/offres_raw/{adzuna,lba}.parquet
    data/processed/{offres,entreprises,scores,candidatures_simulees,p_reponse}.parquet

Par sécurité, le script refuse d'écraser des fichiers existants (qui pourraient être de
vraies données) sauf avec --force.
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from radar.config import FILES, PATHS
from radar.fake_data import generate
from radar.schemas import check_columns


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-n", "--n-entreprises", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true", help="écraser les fichiers existants")
    args = parser.parse_args()

    raw_dir = PATHS.raw / "offres_raw"
    targets = {
        name: FILES[name]
        for name in ("offres", "entreprises", "scores", "candidatures_simulees", "p_reponse")
    }
    raw_targets = {src: raw_dir / f"{src}.parquet" for src in ("adzuna", "lba")}

    existing = [p for p in [*targets.values(), *raw_targets.values()] if p.exists()]
    if existing and not args.force:
        print(
            "Fichiers déjà présents (vraies données ?), rien n'est écrit. Relancer avec --force :"
        )
        for p in existing:
            print(f"  - {p.relative_to(PATHS.root)}")
        return 1

    data = generate(n_entreprises=args.n_entreprises, seed=args.seed)

    raw_dir.mkdir(parents=True, exist_ok=True)
    for src, df in data.offres_raw.items():
        check_columns(df, "offres_raw")
        df.to_parquet(raw_targets[src], index=False)
    for name, path in targets.items():
        df = getattr(data, name)
        check_columns(df, name)
        df.to_parquet(path, index=False)

    print(f"Données FACTICES écrites (graine {args.seed}) :")
    for path in [*raw_targets.values(), *targets.values()]:
        print(
            f"  {path.relative_to(PATHS.root)} : {len(pd.read_parquet(path)):>7,} lignes".replace(
                ",", " "
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
