"""Pipeline complet (T50) : données brutes → entreprises → offres classées et rapprochées → scores.

    uv run python scripts/build_all.py                 # tout reconstruire (sauf collecte)
    uv run python scripts/build_all.py --sirene        # ré-extraire SIRENE aussi (~2 min)
    uv run python scripts/build_all.py --share         # puis partager les fichiers (Onyxia)

Ordre (D10, D13) :
  1. extract_sirene   → data/processed/entreprises.parquet   (si absent ou --sirene)
  2. classify_offres  → data/processed/offres.parquet        (T13 : domaine, contrat, SIRET source)
  3. match_offres     → offres.parquet complété              (T21 : SIRET par nom + position)
  4. build_scores     → data/processed/scores.parquet        (T30 : gamma-Poisson)
La collecte (collect_adzuna.py, collect_lba.py) n'est pas relancée ici : quotas et clés.
Chaque fichier produit est vérifié contre son schéma (radar/schemas.py, D7).
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import time

import pandas as pd

from radar.config import FILES, PATHS
from radar.schemas import check_columns

log = logging.getLogger("build_all")


def step(name: str):
    def deco(fn):
        def run(*a, **k):
            t0 = time.monotonic()
            print(f"\n▶ {name}", flush=True)
            out = fn(*a, **k)
            print(f"  ✓ {name} ({time.monotonic() - t0:.0f} s)", flush=True)
            return out

        return run

    return deco


@step("1. Référentiel SIRENE")
def sirene(force: bool) -> None:
    if FILES["entreprises"].exists() and not force:
        print("  entreprises.parquet présent : conservé (--sirene pour ré-extraire)")
    else:
        from radar.collect.sirene import extract, save

        save(extract())
    check_columns(pd.read_parquet(FILES["entreprises"]), "entreprises")


@step("2. Classification des offres (T13)")
def classify() -> None:
    from radar.process.classify import classify_offers, load_raw_offers

    raw = load_raw_offers()
    if raw.empty:
        sys.exit(
            "Aucune offre dans data/raw/offres_raw/ : lancer un collecteur ou récupérer le parquet."
        )
    print("  sources :", raw["source"].value_counts().to_dict())
    offres = classify_offers(raw)
    offres.to_parquet(FILES["offres"], index=False)


@step("3. Rapprochement SIRET (T21, T25)")
def match() -> None:
    from radar.process.offres import run

    run()
    check_columns(pd.read_parquet(FILES["offres"]), "offres_rapprochees")


@step("4. Scores (T30)")
def scores() -> None:
    from radar.score.build import run

    run()
    check_columns(pd.read_parquet(FILES["scores"]), "scores_reels")


def summary() -> None:
    o = pd.read_parquet(FILES["offres"])
    s = pd.read_parquet(FILES["scores"], columns=["siren", "couverture", "n_offres_domaine_siren"])
    emp = o[~o["intermediaire"].fillna(False)]
    comp = s.drop_duplicates("siren")
    print("\n━━ Résumé ━━")
    print(f"  offres : {len(o):,} ({o['source'].value_counts().to_dict()})")
    print(f"  offres d'employeurs avec SIRET : {emp['siret_match'].notna().mean():.1%}")
    print("  méthodes :", o["match_methode"].value_counts().to_dict())
    covered = (comp["couverture"] > 0).mean()
    print(f"  entreprises notées : {len(comp):,} ; zone couverte : {covered:.1%}")
    print(f"  entreprises avec ≥ 1 offre data : {(comp['n_offres_domaine_siren'] > 0).sum():,}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--sirene", action="store_true", help="ré-extraire SIRENE (~2 min)")
    p.add_argument("--share", action="store_true", help="partager les fichiers produits (Onyxia)")
    args = p.parse_args()
    logging.basicConfig(level=logging.WARNING, format="  %(message)s")

    t0 = time.monotonic()
    sirene(args.sirene)
    classify()
    match()
    scores()
    summary()
    print(f"\nTerminé en {time.monotonic() - t0:.0f} s.")

    if args.share:
        files = [FILES["entreprises"], FILES["offres"], FILES["scores"]]
        cov = PATHS.raw / "offres_raw" / "adzuna_couverture.json"
        files += [cov] if cov.exists() else []
        rel = [str(f.relative_to(PATHS.root)) for f in files]
        # share_s3.py utilise botocore, présent dans le Python d'Onyxia mais pas dans l'env uv
        cmd = ["/usr/bin/env", "-u", "VIRTUAL_ENV", "python3", "scripts/share_s3.py", *rel]
        env_path = ":".join(p for p in os.environ["PATH"].split(":") if ".venv" not in p)
        subprocess.run(cmd, check=True, cwd=PATHS.root, env={**os.environ, "PATH": env_path})


if __name__ == "__main__":
    main()
