"""Collecte La bonne alternance → data/raw/offres_raw/lba.parquet + data/raw/lba_recruteurs.parquet

Exemples :
    uv run python scripts/collect_lba.py                         # export complet (France entière)
    uv run python scripts/collect_lba.py --fichier data/raw/lba/export_XXX.json  # sans réseau
    uv run python scripts/collect_lba.py --search --departements 35 75           # repli
    uv run python scripts/collect_lba.py --search --romes M1405 M1419 M1811      # repli, ROME data

Prérequis : LBA_API_TOKEN dans .env (clé « production » créée sur
https://api.apprentissage.beta.gouv.fr/compte/profil — lecture seule, aucune habilitation requise).
L'export n'est retéléchargé que si La bonne alternance l'a mis à jour (chaque nuit vers 3 h).
"""

import argparse
import logging
from pathlib import Path

from radar.collect.lba import collect_from_export, collect_from_search
from radar.config import PATHS


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--fichier", type=Path, help="export JSON déjà téléchargé (aucun appel)")
    p.add_argument("--force", action="store_true", help="retélécharger l'export")
    p.add_argument("--search", action="store_true", help="repli : /job/v1/search par département")
    p.add_argument("--departements", nargs="*", default=None, help="avec --search (défaut : tous)")
    p.add_argument("--romes", nargs="*", default=None, help="avec --search : codes ROME")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.search:
        offres, recs = collect_from_search(args.departements, args.romes)
    else:
        offres, recs = collect_from_export(args.fichier, force_download=args.force)

    out_offres = PATHS.raw / "offres_raw" / "lba.parquet"
    out_recs = PATHS.raw / "lba_recruteurs.parquet"
    out_offres.parent.mkdir(parents=True, exist_ok=True)
    offres.to_parquet(out_offres, index=False)
    recs.to_parquet(out_recs, index=False)

    n_siret = offres["siret"].notna().mean() if len(offres) else 0
    print(f"\n{len(offres)} offres → {out_offres.relative_to(PATHS.root)}")
    print(
        f"   SIRET renseigné : {n_siret:.0%} ; déléguées à une école : "
        f"{int(offres['delegue_ecole'].sum())}"
    )
    print(f"{len(recs)} recruteurs potentiels → {out_recs.relative_to(PATHS.root)}")
    if len(offres):
        print("   Statuts :", offres["statut"].value_counts(dropna=False).to_dict())
        print("   Partenaires :", offres["partenaire"].value_counts().head(8).to_dict())


if __name__ == "__main__":
    main()
