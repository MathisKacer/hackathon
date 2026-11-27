"""Extraction SIRENE → data/processed/entreprises.parquet (T20).

    uv run python scripts/extract_sirene.py

Lit ~2 Go de parquet à distance (seules les colonnes utiles sont téléchargées) : compter
quelques minutes. Aucune clé nécessaire. Ensuite, partager le fichier avec l'équipe :
    python3 scripts/share_s3.py data/processed/entreprises.parquet
"""

import logging

from radar.collect.sirene import extract, save
from radar.config import FILES, PATHS


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    df = extract()
    save(df)
    print(f"\n{len(df):,} établissements → {FILES['entreprises'].relative_to(PATHS.root)}")
    print(f"  géolocalisés           : {df['lat'].notna().mean():.1%}")
    print(f"  avec nom               : {df['nom'].notna().mean():.1%}")
    print(f"  avec libellé NAF       : {df['naf_libelle'].notna().mean():.1%}")
    print(f"  diffusion partielle    : {df['diffusion_partielle'].sum():,} (position masquée)")
    print("  par catégorie          :", df["categorie"].value_counts(dropna=False).to_dict())


if __name__ == "__main__":
    main()
