"""T77 — Remplir la grille secteur × taille × domaine avec un LLM (API compatible OpenAI).

    # Ollama sur CPU (petit modèle, test) :
    uv run python scripts/build_grille_llm.py --model qwen2.5:7b --limit 20
    # vLLM sur GPU :
    uv run python scripts/build_grille_llm.py --base-url http://localhost:8000/v1 \\
        --model Qwen/Qwen2.5-14B-Instruct --workers 16
    # Exporter la liste des NAF (pour Google Colab, sans entreprises.parquet) :
    uv run python scripts/build_grille_llm.py --export-naf data/naf_liste.csv
    # Sur Colab (voir notebooks/grille_llm_colab.ipynb) :
    python scripts/build_grille_llm.py --naf-csv naf_liste.csv --cache-dir /content/drive/... \\
        --model qwen2.5:14b

Cache par NAF : on peut interrompre et relancer. Écrit data/processed/grille_domaines.parquet
(uniquement les NAF déjà notés) et liste les NAF en échec.
"""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

import pandas as pd

from radar.config import FILES
from radar.score import llm_grid
from radar.score.llm_grid import GRID_FILE, LLMClient, naf_table, rate_all, to_long


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--base-url", default="http://localhost:11434/v1")
    p.add_argument("--model", default="qwen2.5:7b")
    p.add_argument("--limit", type=int, help="seulement les N NAF les plus fréquents")
    p.add_argument("--workers", type=int, default=4, help="requêtes en parallèle")
    p.add_argument("--naf-csv", type=Path, help="liste des NAF (au lieu d'entreprises.parquet)")
    p.add_argument("--cache-dir", type=Path, help="dossier du cache (ex. Google Drive)")
    p.add_argument("--out", type=Path, default=GRID_FILE, help="grille en sortie (parquet)")
    p.add_argument("--export-naf", type=Path, help="écrire la liste des NAF en CSV et s'arrêter")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    if a.naf_csv:
        nafs = pd.read_csv(a.naf_csv, dtype={"naf": str})
    else:
        nafs = naf_table(pd.read_parquet(FILES["entreprises"]))
    if a.export_naf:
        a.export_naf.parent.mkdir(parents=True, exist_ok=True)
        nafs.to_csv(a.export_naf, index=False)
        print(f"{len(nafs)} NAF → {a.export_naf}")
        return
    if a.cache_dir:
        llm_grid.CACHE_DIR = a.cache_dir
    nafs = nafs.sort_values("n_etab", ascending=False)
    if a.limit:
        nafs = nafs.head(a.limit)
    t0 = time.time()
    done, failed = rate_all(LLMClient(a.base_url, a.model), nafs, a.workers)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    to_long(done).to_parquet(a.out, index=False)
    print(f"{len(done)} NAF notés, {len(failed)} en échec, {time.time() - t0:.0f} s → {a.out}")
    if failed:
        print("En échec (relancer la commande) :", ", ".join(failed))


if __name__ == "__main__":
    main()
