"""Administrateurs et gestion des comptes (T79, D39).

    con = accounts.connect()
    admin.ensure_schema(con)
    admin.set_admin(con, "maxence", True)            # SEULEMENT depuis scripts/admin.py
    admin.list_users(con)                            # nombres seulement, jamais de contenu
    admin.unlock(con, admin_id, target_id)
    temp = admin.reset_password(con, admin_id, target_id)   # mot de passe provisoire
    admin.delete_account(con, admin_id, target_id)
    admin.change_password(con, user_id, ancien, nouveau)    # pour tout le monde

Règles :
- **Seuls les membres de l'équipe sont administrateurs** (au plus `MAX_ADMINS` = 4). On le
  devient **uniquement** par `scripts/admin.py`, lancé dans le terminal du pod : jamais depuis
  le site, et aucun identifiant n'est écrit dans le code (sinon le premier venu qui crée le
  compte « maxence » deviendrait administrateur).
- Un administrateur gère les **comptes classiques** : il peut débloquer n'importe quel compte,
  mais ne réinitialise ni ne supprime le compte d'un autre administrateur (ça se règle entre
  membres de l'équipe, par le script).
- **Vie privée** : l'administrateur voit des nombres (recherches, favoris), jamais leur contenu.
- Chaque action est inscrite dans le journal `admin_log` (qui, quoi, sur quel compte, quand).
"""

from __future__ import annotations

import secrets
import sqlite3
import string
from datetime import UTC, datetime

import pandas as pd

from radar.accounts import (
    AccountError,
    _now,
    hash_password,
    normalize_username,
    password_problems,
    verify_password,
)

MAX_ADMINS = 4  # les quatre membres de l'équipe
TERMINAL = "(terminal)"  # auteur des actions faites par scripts/admin.py

_ADMIN_SCHEMA = """
CREATE TABLE IF NOT EXISTS admin_log (
    id         INTEGER PRIMARY KEY,
    created_at TEXT    NOT NULL,
    admin      TEXT    NOT NULL,
    action     TEXT    NOT NULL,
    cible      TEXT    NOT NULL,
    details    TEXT    NOT NULL DEFAULT ''
);
"""


def ensure_schema(con: sqlite3.Connection) -> None:
    """Colonnes `is_admin`, `must_change_password` et table `admin_log` (bases existantes aussi)."""
    cols = {r[1] for r in con.execute("PRAGMA table_info(users)")}
    with con:
        if "is_admin" not in cols:
            con.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
        if "must_change_password" not in cols:
            con.execute(
                "ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0"
            )
        con.executescript(_ADMIN_SCHEMA)


def _log(con: sqlite3.Connection, admin: str, action: str, cible: str, details: str = "") -> None:
    con.execute(
        "INSERT INTO admin_log (created_at, admin, action, cible, details) VALUES (?, ?, ?, ?, ?)",
        (_now(), admin, action, cible, details),
    )


def _user(con: sqlite3.Connection, user_id: int) -> tuple[int, str, bool] | None:
    row = con.execute(
        "SELECT id, username, is_admin FROM users WHERE id = ?", (int(user_id),)
    ).fetchone()
    return (int(row[0]), row[1], bool(row[2])) if row else None


def is_admin(con: sqlite3.Connection, user_id: int | None) -> bool:
    if user_id is None:
        return False
    ensure_schema(con)
    u = _user(con, user_id)
    return bool(u and u[2])


def _require_admin(con: sqlite3.Connection, admin_id: int) -> str:
    """Nom de l'administrateur ; refuse si l'auteur n'est pas (ou plus) administrateur."""
    ensure_schema(con)
    u = _user(con, admin_id)
    if not (u and u[2]):
        raise AccountError("Action réservée aux administrateurs.")
    return u[1]


def _classic_target(con: sqlite3.Connection, target_id: int, action: str) -> str:
    u = _user(con, target_id)
    if u is None:
        raise AccountError("Ce compte n'existe plus.")
    if u[2]:
        raise AccountError(
            f"Impossible de {action} le compte d'un administrateur depuis le site "
            "(à régler entre membres de l'équipe avec scripts/admin.py)."
        )
    return u[1]


# --- Script (terminal du pod) seulement ---------------------------------------------------


def set_admin(con: sqlite3.Connection, username: str, flag: bool) -> None:
    """Nomme ou retire un administrateur. À n'appeler que depuis scripts/admin.py."""
    ensure_schema(con)
    name = normalize_username(username)
    row = con.execute("SELECT id, is_admin FROM users WHERE username = ?", (name,)).fetchone()
    if row is None:
        raise AccountError(f"Aucun compte « {name} » : crée-le d'abord dans l'app.")
    if flag and not row[1]:
        n = con.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1").fetchone()[0]
        if n >= MAX_ADMINS:
            raise AccountError(f"Déjà {MAX_ADMINS} administrateurs (les membres de l'équipe).")
    with con:
        con.execute("UPDATE users SET is_admin = ? WHERE id = ?", (int(flag), row[0]))
        _log(con, TERMINAL, "nommé administrateur" if flag else "retiré des administrateurs", name)


# --- Page Administration ------------------------------------------------------------------


def list_users(con: sqlite3.Connection, now: datetime | None = None) -> pd.DataFrame:
    """Comptes avec des **nombres** seulement (vie privée : pas le contenu)."""
    ensure_schema(con)
    now = now or datetime.now(UTC)
    df = pd.read_sql_query(
        """
        SELECT u.id, u.username, u.created_at, u.is_admin, u.locked_until,
               u.must_change_password,
               (SELECT COUNT(*) FROM recherches r WHERE r.user_id = u.id) AS n_recherches,
               (SELECT COUNT(*) FROM favoris f WHERE f.user_id = u.id) AS n_favoris,
               EXISTS (SELECT 1 FROM profils p WHERE p.user_id = u.id) AS a_profil
        FROM users u ORDER BY u.is_admin DESC, u.created_at
        """,
        con,
    )
    locked = pd.to_datetime(df["locked_until"], utc=True, errors="coerce")
    df["bloque"] = locked.notna() & (locked > pd.Timestamp(now))
    for c in ("is_admin", "must_change_password", "a_profil"):
        df[c] = df[c].astype(bool)
    return df.drop(columns="locked_until")


def unlock(con: sqlite3.Connection, admin_id: int, target_id: int) -> None:
    admin = _require_admin(con, admin_id)
    u = _user(con, target_id)
    if u is None:
        raise AccountError("Ce compte n'existe plus.")
    with con:
        con.execute("UPDATE users SET failed_logins = 0, locked_until = NULL WHERE id = ?", (u[0],))
        _log(con, admin, "débloqué", u[1])


def temporary_password(length: int = 16) -> str:
    """Mot de passe provisoire aléatoire qui respecte les règles (D16)."""
    alphabet = string.ascii_letters + string.digits + "-_.!?"
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if not password_problems(pwd):
            return pwd


def reset_password(con: sqlite3.Connection, admin_id: int, target_id: int) -> str:
    """Nouveau mot de passe provisoire (renvoyé une seule fois, jamais stocké en clair)."""
    admin = _require_admin(con, admin_id)
    name = _classic_target(con, target_id, "réinitialiser")
    pwd = temporary_password()
    with con:
        con.execute(
            "UPDATE users SET password_hash = ?, must_change_password = 1, failed_logins = 0, "
            "locked_until = NULL WHERE id = ?",
            (hash_password(pwd), int(target_id)),
        )
        _log(con, admin, "mot de passe réinitialisé", name)
    return pwd


def delete_account(con: sqlite3.Connection, admin_id: int, target_id: int) -> None:
    admin = _require_admin(con, admin_id)
    if int(admin_id) == int(target_id):
        raise AccountError("Pour supprimer ton propre compte, passe par Mon espace.")
    name = _classic_target(con, target_id, "supprimer")
    with con:
        con.execute("DELETE FROM users WHERE id = ?", (int(target_id),))
        _log(con, admin, "compte supprimé", name)


def list_log(con: sqlite3.Connection, limit: int = 50) -> pd.DataFrame:
    ensure_schema(con)
    return pd.read_sql_query(
        "SELECT created_at, admin, action, cible, details FROM admin_log ORDER BY id DESC LIMIT ?",
        con,
        params=(int(limit),),
    )


# --- Pour tout le monde -------------------------------------------------------------------


def must_change_password(con: sqlite3.Connection, user_id: int) -> bool:
    ensure_schema(con)
    row = con.execute(
        "SELECT must_change_password FROM users WHERE id = ?", (int(user_id),)
    ).fetchone()
    return bool(row and row[0])


def change_password(con: sqlite3.Connection, user_id: int, old: str, new: str) -> None:
    """Change son mot de passe (ancien vérifié, mêmes règles qu'à la création)."""
    ensure_schema(con)
    row = con.execute(
        "SELECT username, password_hash FROM users WHERE id = ?", (int(user_id),)
    ).fetchone()
    if row is None:
        raise AccountError("Ce compte n'existe plus.")
    if not verify_password(old, row[1]):
        raise AccountError("Mot de passe actuel incorrect.")
    if new == old:
        raise AccountError("Le nouveau mot de passe doit être différent de l'actuel.")
    problems = password_problems(new, row[0])
    if problems:
        raise AccountError("Mot de passe refusé : " + " ; ".join(problems) + ".")
    with con:
        con.execute(
            "UPDATE users SET password_hash = ?, must_change_password = 0 WHERE id = ?",
            (hash_password(new), int(user_id)),
        )
