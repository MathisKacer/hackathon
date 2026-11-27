"""Collecte des offres Adzuna → data/raw/offres_raw/adzuna.parquet

Exemples :
    uv run python scripts/collect_adzuna.py                      # toutes les régions, quota du jour
    uv run python scripts/collect_adzuna.py --regions Bretagne   # une seule région
    uv run python scripts/collect_adzuna.py --max-calls 10       # plafonner les appels réels
    uv run python scripts/collect_adzuna.py --quota              # afficher le quota consommé

Relancer la commande est sans risque : les pages déjà téléchargées viennent du cache (gratuit),
seules les pages manquantes consomment du quota. Relancer chaque jour pour compléter la France.
"""

import argparse
import json
import logging

from radar.collect.adzuna import DEFAULT_DAILY_LIMIT, REGIONS, Quota, collect
from radar.config import PATHS


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--what", default="data", help="mots-clés Adzuna (défaut : data)")
    p.add_argument("--regions", nargs="*", default=None, help=f"défaut : {', '.join(REGIONS)}")
    p.add_argument("--max-days-old", type=int, default=60)
    p.add_argument("--daily-limit", type=int, default=DEFAULT_DAILY_LIMIT)
    p.add_argument("--max-calls", type=int, default=None, help="plafond d'appels réels")
    p.add_argument("--quota", action="store_true", help="affiche le quota du jour et quitte")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.quota:
        q = Quota(args.daily_limit)
        print(f"Appels réels aujourd'hui (UTC) : {q.used_today} / {q.daily_limit}")
        return

    df = collect(args.what, args.regions, args.max_days_old, args.daily_limit, args.max_calls)
    out = PATHS.raw / "offres_raw" / "adzuna.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    # Couverture par région : sert au score (exposition pondérée, T30).
    (out.parent / "adzuna_couverture.json").write_text(
        json.dumps(
            {
                "date_collecte": df["date_collecte"].max() if len(df) else None,
                "requete": args.what,
                "max_days_old": args.max_days_old,
                "regions": df.attrs["coverage"],
            },
            ensure_ascii=False,
            indent=1,
        )
    )

    print(f"\n{len(df)} offres uniques → {out.relative_to(PATHS.root)}")
    print(
        f"Appels réels cette exécution : {df.attrs['real_calls']} "
        f"(aujourd'hui : {df.attrs['quota_used_today']})"
    )
    for region, s in df.attrs["status"].items():
        print(f"  {region:28} {s}")


if __name__ == "__main__":
    main()
