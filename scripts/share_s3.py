"""Partage de fichiers de données avec l'équipe (y compris hors Onyxia) via S3 SSP Cloud.

Dépose les fichiers dans l'espace S3 **privé** de l'utilisateur Onyxia, puis affiche un lien de
téléchargement temporaire (presigned URL) par fichier. Quiconque a le lien peut télécharger le
fichier, sans compte ; le fichier n'est listé nulle part et le lien expire.

⚠️ Ne jamais publier ces fichiers dans le dépôt GitHub (public) ni dans `diffusion/` (public) :
les offres Adzuna ne doivent pas être redistribuées publiquement. Partager les liens en privé.

À lancer depuis un service Onyxia (identifiants S3 dans l'environnement) :
    python3 scripts/share_s3.py data/raw/offres_raw/adzuna.parquet
    python3 scripts/share_s3.py data/processed/entreprises.parquet --hours 12

Côté coéquipier (n'importe quelle machine), depuis la racine du dépôt :
    curl -o data/raw/offres_raw/adzuna.parquet "<lien>"
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _client():
    import botocore.session
    from botocore.config import Config

    missing = [
        v
        for v in ("AWS_S3_ENDPOINT", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")
        if v not in os.environ
    ]
    if missing:
        sys.exit(
            f"Identifiants S3 absents ({', '.join(missing)}) : lancer depuis un service Onyxia."
        )
    return botocore.session.get_session().create_client(
        "s3",
        endpoint_url="https://" + os.environ["AWS_S3_ENDPOINT"].removeprefix("https://"),
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
        config=Config(signature_version="s3v4", connect_timeout=10, read_timeout=60),
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("files", nargs="+", type=Path, help="fichiers sous data/")
    p.add_argument("--hours", type=int, default=24, help="durée de validité des liens (défaut 24)")
    p.add_argument(
        "--bucket", default=os.environ.get("VAULT_TOP_DIR"), help="espace S3 (défaut : le tien)"
    )
    args = p.parse_args()
    if not args.bucket:
        sys.exit("Espace S3 inconnu : préciser --bucket <ton identifiant Onyxia>.")

    s3 = _client()
    for f in args.files:
        f = f.resolve()
        rel = f.relative_to(ROOT).as_posix()
        if not rel.startswith("data/") or "data/cache" in rel:
            sys.exit(
                f"Refusé : {rel} (seuls les fichiers de data/ hors data/cache/ sont partageables)"
            )
        key = f"radar/{rel}"
        s3.put_object(Bucket=args.bucket, Key=key, Body=f.read_bytes())
        url = s3.generate_presigned_url(
            "get_object", Params={"Bucket": args.bucket, "Key": key}, ExpiresIn=args.hours * 3600
        )
        print(f"\n# {rel} ({f.stat().st_size / 1e6:.1f} Mo), lien valable {args.hours} h")
        print(f'curl -o {rel} "{url}"')


if __name__ == "__main__":
    main()
