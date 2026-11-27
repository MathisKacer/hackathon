"""Comptes facultatifs (T48, T49, D14) : utilisateurs, profils et historique, en SQLite local.

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
    log_search(con, user_id, {"contrat": "Stage"}, n_results=42, top=["ACME"])  # T49
    list_searches(con, user_id)                                 # plus récentes d'abord
    delete_user(con, user_id)                                   # efface compte, profil, historique
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from radar.config import PATHS

DB_PATH = PATHS.data / "app" / "radar.db"

USERNAME_RE = re.compile(r"^[a-z0-9._-]{3,30}$")
PASSWORD_MIN, PASSWORD_MAX = 8, 128
PROFILE_MAX_BYTES = 10_000

# Historique (T49). Streamlit relance la page à chaque changement de réglage : les changements
# faits à moins de SEARCH_MERGE_WINDOW de la dernière recherche la mettent à jour au lieu
# d'en créer une nouvelle (on garde l'état final, pas chaque cran de curseur).
SEARCH_MERGE_WINDOW = timedelta(minutes=2)
SEARCH_MAX_PER_USER = 50
SEARCH_TOP_MAX = 5

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
CREATE TABLE IF NOT EXISTS recherches (
    id            INTEGER PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at    TEXT    NOT NULL,
    params        TEXT    NOT NULL,
    n_resultats   INTEGER NOT NULL,
    top_resultats TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS recherches_user ON recherches (user_id, created_at);
"""


class AccountError(ValueError):
    """Erreur affichable telle quelle (identifiant pris, mot de passe trop court…)."""


def _now(now: datetime | None = None) -> str:
    return (now or datetime.now(UTC)).isoformat(timespec="seconds")


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
    """Supprime le compte et tout ce qui lui est rattaché (profil, historique)."""
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


# --- Historique des recherches (T49) -----------------------------------------------------


def _dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def log_search(
    con: sqlite3.Connection,
    user_id: int,
    params: dict,
    n_results: int,
    top: list[str] | None = None,
    now: datetime | None = None,
) -> int:
    """Enregistre une recherche ; renvoie son id.

    Fusionne avec la dernière recherche si les paramètres sont identiques, ou si elle date de
    moins de SEARCH_MERGE_WINDOW (réglages en cours d'ajustement). `top` : quelques résultats
    à afficher dans l'historique (noms d'entreprises, ou SIRET quand T40 sera là).
    """
    if not isinstance(params, dict):
        raise AccountError("Les paramètres de recherche doivent être un dictionnaire.")
    params_json = _dump(params)
    if len(params_json.encode()) > PROFILE_MAX_BYTES:
        raise AccountError("Recherche trop volumineuse.")
    top_json = _dump([str(t) for t in (top or [])][:SEARCH_TOP_MAX])
    now = now or datetime.now(UTC)
    last = con.execute(
        "SELECT id, created_at, params FROM recherches WHERE user_id = ? "
        "ORDER BY created_at DESC, id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    with con:
        if last and (
            last[2] == params_json or now - datetime.fromisoformat(last[1]) < SEARCH_MERGE_WINDOW
        ):
            con.execute(
                "UPDATE recherches SET created_at = ?, params = ?, n_resultats = ?, "
                "top_resultats = ? WHERE id = ?",
                (_now(now), params_json, int(n_results), top_json, last[0]),
            )
            search_id = last[0]
        else:
            cur = con.execute(
                "INSERT INTO recherches (user_id, created_at, params, n_resultats, top_resultats) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, _now(now), params_json, int(n_results), top_json),
            )
            search_id = cur.lastrowid
        # On ne garde que les SEARCH_MAX_PER_USER plus récentes.
        con.execute(
            """DELETE FROM recherches WHERE user_id = ? AND id NOT IN (
                   SELECT id FROM recherches WHERE user_id = ?
                   ORDER BY created_at DESC, id DESC LIMIT ?)""",
            (user_id, user_id, SEARCH_MAX_PER_USER),
        )
    return int(search_id)


def list_searches(con: sqlite3.Connection, user_id: int, limit: int = 20) -> list[dict]:
    """Recherches de l'utilisateur, les plus récentes d'abord."""
    rows = con.execute(
        "SELECT id, created_at, params, n_resultats, top_resultats FROM recherches "
        "WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    return [
        {
            "id": r[0],
            "created_at": datetime.fromisoformat(r[1]),
            "params": json.loads(r[2]),
            "n_resultats": r[3],
            "top_resultats": json.loads(r[4]),
        }
        for r in rows
    ]


def clear_searches(con: sqlite3.Connection, user_id: int) -> None:
    with con:
        con.execute("DELETE FROM recherches WHERE user_id = ?", (user_id,))
