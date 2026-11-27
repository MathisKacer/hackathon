"""Comptes facultatifs (T48, D14) : utilisateurs et profils, dans une base SQLite locale.

Le mode démo anonyme n'appelle jamais ce module : rien n'est écrit tant qu'on ne se connecte pas.

- Mots de passe hachés avec scrypt (bibliothèque standard), sel aléatoire par compte ;
  jamais stockés ni journalisés en clair.
- Profil = dictionnaire JSON des réglages de recherche (domaine, contrat, adresse, rayon,
  filtres, poids…). Le module ne connaît pas les clés : c'est l'app qui décide quoi enregistrer.
- Base : data/app/radar.db (ignorée par Git). Un pod Onyxia est éphémère : la base est
  perdue au redémarrage (acceptable pour la démo, voir docs/LIMITES.md).

Usage :
    con = connect()
    user_id = create_user(con, "celia", "un mot de passe")
    user_id = authenticate(con, "celia", "un mot de passe")   # None si incorrect
    save_profile(con, user_id, {"contrat": "Stage", "rayon_km": 20})
    load_profile(con, user_id)                                  # {} si aucun profil
    delete_user(con, user_id)                                   # efface le compte et le profil
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from radar.config import PATHS

DB_PATH = PATHS.data / "app" / "radar.db"

USERNAME_RE = re.compile(r"^[a-z0-9._-]{3,30}$")
PASSWORD_MIN, PASSWORD_MAX = 8, 128
PROFILE_MAX_BYTES = 10_000

# scrypt : paramètres recommandés pour un usage interactif (~50 ms, 16 Mo de mémoire).
_SCRYPT = {"n": 2**14, "r": 8, "p": 1}

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL
);
CREATE TABLE IF NOT EXISTS profils (
    user_id    INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    data       TEXT    NOT NULL,
    updated_at TEXT    NOT NULL
);
"""


class AccountError(ValueError):
    """Erreur affichable telle quelle (identifiant pris, mot de passe trop court…)."""


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


# --- Mots de passe ------------------------------------------------------------------------


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, **_SCRYPT)
    return f"scrypt${_SCRYPT['n']}${_SCRYPT['r']}${_SCRYPT['p']}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt, digest = stored.split("$")
    except ValueError:
        return False
    if algo != "scrypt":
        return False
    candidate = hashlib.scrypt(
        password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p)
    )
    return hmac.compare_digest(candidate, bytes.fromhex(digest))


# Haché factice : vérifié quand l'identifiant n'existe pas, pour que le temps de réponse
# ne révèle pas si un compte existe.
_DUMMY_HASH = hash_password(secrets.token_hex(16))


# --- Base ---------------------------------------------------------------------------------


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Ouvre (et crée si besoin) la base des comptes."""
    path = Path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    # check_same_thread=False : Streamlit peut servir une session sur plusieurs threads.
    con = sqlite3.connect(path, check_same_thread=False)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    return con


def normalize_username(username: str) -> str:
    return username.strip().lower()


def create_user(con: sqlite3.Connection, username: str, password: str) -> int:
    username = normalize_username(username)
    if not USERNAME_RE.fullmatch(username):
        raise AccountError(
            "Identifiant invalide : 3 à 30 caractères parmi lettres, chiffres, "
            "« . », « _ » et « - »."
        )
    if not PASSWORD_MIN <= len(password) <= PASSWORD_MAX:
        raise AccountError(f"Le mot de passe doit faire au moins {PASSWORD_MIN} caractères.")
    try:
        with con:
            cur = con.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, hash_password(password), _now()),
            )
    except sqlite3.IntegrityError:
        raise AccountError("Cet identifiant est déjà pris.") from None
    return int(cur.lastrowid)


def authenticate(con: sqlite3.Connection, username: str, password: str) -> int | None:
    """Renvoie l'id de l'utilisateur, ou None si l'identifiant ou le mot de passe est faux."""
    row = con.execute(
        "SELECT id, password_hash FROM users WHERE username = ?", (normalize_username(username),)
    ).fetchone()
    if row is None:
        verify_password(password, _DUMMY_HASH)
        return None
    return int(row[0]) if verify_password(password, row[1]) else None


def get_username(con: sqlite3.Connection, user_id: int) -> str | None:
    row = con.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    return row[0] if row else None


def delete_user(con: sqlite3.Connection, user_id: int) -> None:
    """Supprime le compte et tout ce qui lui est rattaché (profil ; historique avec T49)."""
    with con:
        con.execute("DELETE FROM users WHERE id = ?", (user_id,))


# --- Profil -------------------------------------------------------------------------------


def save_profile(con: sqlite3.Connection, user_id: int, profile: dict) -> None:
    if not isinstance(profile, dict):
        raise AccountError("Le profil doit être un dictionnaire.")
    data = json.dumps(profile, ensure_ascii=False, sort_keys=True)
    if len(data.encode()) > PROFILE_MAX_BYTES:
        raise AccountError("Profil trop volumineux.")
    with con:
        con.execute(
            """INSERT INTO profils (user_id, data, updated_at) VALUES (?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET data = excluded.data,
                                                  updated_at = excluded.updated_at""",
            (user_id, data, _now()),
        )


def load_profile(con: sqlite3.Connection, user_id: int) -> dict:
    row = con.execute("SELECT data FROM profils WHERE user_id = ?", (user_id,)).fetchone()
    return json.loads(row[0]) if row else {}
