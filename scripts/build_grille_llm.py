"""T77 — Remplir la grille secteur × taille × domaine avec un LLM (API compatible OpenAI).

    # Ollama sur CPU (petit modèle, test) :
    uv run python scripts/build_grille_llm.py --model qwen2.5:7b --limit 20
    # vLLM sur GPU :
    uv run python scripts/build_grille_llm.py --base-url http://localhost:8000/v1 \\
        --model Qwen/Qwen2.5-14B-Instruct --workers 16

Cache par NAF : on peut interrompre et relancer. Écrit data/processed/grille_domaines.parquet
(uniquement les NAF déjà notés) et liste les NAF en échec.
"""

from __future__ import annotations

import argparse
import logging
import time

import pandas as pd

from radar.config import FILES
from radar.score.llm_grid import GRID_FILE, LLMClient, naf_table, rate_all, to_long


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--base-url", default="http://localhost:11434/v1")
    p.add_argument("--model", default="qwen2.5:7b")
    p.add_argument("--limit", type=int, help="seulement les N NAF les plus fréquents")
    p.add_argument("--workers", type=int, default=4, help="requêtes en parallèle")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    nafs = naf_table(pd.read_parquet(FILES["entreprises"]))
    if a.limit:
        nafs = nafs.head(a.limit)
    t0 = time.time()
    done, failed = rate_all(LLMClient(a.base_url, a.model), nafs, a.workers)
    long = to_long(done)
    long.to_parquet(GRID_FILE, index=False)
    print(
        f"{len(done)} NAF notés, {len(failed)} en échec, {time.time() - t0:.0f} s "
        f"→ {GRID_FILE.name}"
    )
    if failed:
        print("En échec (relancer la commande) :", ", ".join(failed))


if __name__ == "__main__":
    main()
