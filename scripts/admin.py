"""Nommer ou retirer les administrateurs de Radar (T79, D39) — terminal du pod seulement.

    uv run python scripts/admin.py liste                  # comptes et administrateurs
    uv run python scripts/admin.py promouvoir maxence     # le compte doit déjà exister
    uv run python scripts/admin.py retirer maxence
    uv run python scripts/admin.py journal                # dernières actions d'administration

Seuls les membres de l'équipe (au plus 4) sont administrateurs : ce script est le **seul**
moyen d'en nommer, l'app ne le permet pas. La base est celle du pod (data/app/radar.db, L17) :
chacun nomme les administrateurs sur son propre pod.
"""

from __future__ import annotations

import argparse
import sys

from radar import accounts, admin


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("liste", help="lister les comptes")
    for name in ("promouvoir", "retirer"):
        p = sub.add_parser(name, help=f"{name} un administrateur")
        p.add_argument("identifiant")
    sub.add_parser("journal", help="dernières actions d'administration")
    args = parser.parse_args(argv)

    con = accounts.connect()
    admin.ensure_schema(con)
    try:
        if args.cmd == "liste":
            users = admin.list_users(con)
            if users.empty:
                print("Aucun compte. Crée d'abord ton compte dans l'app (Mon espace).")
            for _, u in users.iterrows():
                role = "ADMIN" if u["is_admin"] else "     "
                lock = " (bloqué)" if u["bloque"] else ""
                print(f"{role}  {u['username']:<30} créé le {u['created_at'][:10]}{lock}")
            print(f"\n{int(users['is_admin'].sum())} administrateur(s) sur {admin.MAX_ADMINS} max.")
        elif args.cmd == "journal":
            log = admin.list_log(con)
            print(log.to_string(index=False) if not log.empty else "Journal vide.")
        else:
            admin.set_admin(con, args.identifiant, args.cmd == "promouvoir")
            verbe = "est maintenant" if args.cmd == "promouvoir" else "n'est plus"
            print(f"« {accounts.normalize_username(args.identifiant)} » {verbe} administrateur.")
    except accounts.AccountError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
