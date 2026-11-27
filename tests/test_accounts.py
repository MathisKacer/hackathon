"""Tests des comptes facultatifs (T48). Base SQLite temporaire, jamais data/app/radar.db."""

from datetime import UTC, datetime, timedelta

import pytest

from radar.accounts import (
    LOGIN_LOCK_DURATION,
    LOGIN_MAX_FAILS,
    SEARCH_MAX_PER_USER,
    AccountError,
    AccountLocked,
    authenticate,
    clear_searches,
    connect,
    create_user,
    delete_user,
    get_username,
    hash_password,
    list_searches,
    load_profile,
    log_search,
    password_problems,
    save_profile,
    verify_password,
)


@pytest.fixture
def con(tmp_path):
    c = connect(tmp_path / "radar.db")
    yield c
    c.close()


def test_password_hash_is_salted_and_verifiable():
    h1, h2 = hash_password("Radar-Demo-2026"), hash_password("Radar-Demo-2026")
    assert h1 != h2  # sel aléatoire
    assert "Radar-Demo-2026" not in h1
    assert verify_password("Radar-Demo-2026", h1)
    assert not verify_password("mauvais", h1)
    assert not verify_password("Radar-Demo-2026", "pas-un-hache")


def test_create_and_authenticate(con):
    uid = create_user(con, "  Celia ", "Radar-Demo-2026")
    assert get_username(con, uid) == "celia"  # identifiant normalisé
    assert authenticate(con, "CELIA", "Radar-Demo-2026") == uid
    assert authenticate(con, "celia", "mauvais") is None
    assert authenticate(con, "inconnu", "Radar-Demo-2026") is None


def test_password_never_stored_in_clear(con):
    create_user(con, "celia", "Radar-Demo-2026")
    stored = con.execute("SELECT password_hash FROM users").fetchone()[0]
    assert "Radar-Demo-2026" not in stored and stored.startswith("scrypt$")


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("ab", "Radar-Demo-2026"),
        ("nom avec espace", "Radar-Demo-2026"),
        ("x" * 31, "Radar-Demo-2026"),
        ("celia", "court"),
        ("celia", "x" * 129),
    ],
)
def test_invalid_credentials_rejected(con, username, password):
    with pytest.raises(AccountError):
        create_user(con, username, password)


def test_duplicate_username_rejected(con):
    create_user(con, "celia", "Radar-Demo-2026")
    with pytest.raises(AccountError, match="déjà pris"):
        create_user(con, "CELIA", "Encore-Un-Mdp-7")


def test_profile_roundtrip_and_update(con):
    uid = create_user(con, "celia", "Radar-Demo-2026")
    assert load_profile(con, uid) == {}
    save_profile(con, uid, {"contrat": "Stage", "regions": ["Bretagne"], "max_age": 30})
    assert load_profile(con, uid) == {"contrat": "Stage", "regions": ["Bretagne"], "max_age": 30}
    save_profile(con, uid, {"contrat": "Alternance"})
    assert load_profile(con, uid) == {"contrat": "Alternance"}


def test_profile_size_limit(con):
    uid = create_user(con, "celia", "Radar-Demo-2026")
    with pytest.raises(AccountError):
        save_profile(con, uid, {"x": "a" * 20_000})


def test_profiles_are_isolated(con):
    a = create_user(con, "celia", "Radar-Demo-2026")
    b = create_user(con, "mathis", "Autre-Compte-42")
    save_profile(con, a, {"contrat": "Stage"})
    assert load_profile(con, b) == {}


def test_delete_user_removes_profile(con):
    uid = create_user(con, "celia", "Radar-Demo-2026")
    save_profile(con, uid, {"contrat": "Stage"})
    delete_user(con, uid)
    assert get_username(con, uid) is None
    assert authenticate(con, "celia", "Radar-Demo-2026") is None
    assert con.execute("SELECT count(*) FROM profils").fetchone()[0] == 0
    create_user(con, "celia", "Nouveau-Mdp-2026")  # l'identifiant redevient libre


# --- Historique (T49) ---------------------------------------------------------------------

T0 = datetime(2026, 11, 27, 15, 0, tzinfo=UTC)


def test_log_and_list_searches(con):
    uid = create_user(con, "celia", "Radar-Demo-2026")
    assert list_searches(con, uid) == []
    log_search(con, uid, {"contrat": "Stage"}, 12, ["ACME", "BETA"], now=T0)
    log_search(con, uid, {"contrat": "Alternance"}, 3, now=T0 + timedelta(minutes=10))
    hist = list_searches(con, uid)
    assert [h["params"]["contrat"] for h in hist] == ["Alternance", "Stage"]  # récentes d'abord
    assert hist[1]["n_resultats"] == 12 and hist[1]["top_resultats"] == ["ACME", "BETA"]
    assert hist[0]["created_at"] == T0 + timedelta(minutes=10)


def test_quick_adjustments_are_merged(con):
    """Bouger un curseur : chaque cran relance la page, une seule recherche est gardée."""
    uid = create_user(con, "celia", "Radar-Demo-2026")
    for i, days in enumerate((60, 53, 46, 39)):
        log_search(con, uid, {"max_age": days}, 100 - i, now=T0 + timedelta(seconds=10 * i))
    hist = list_searches(con, uid)
    assert len(hist) == 1 and hist[0]["params"] == {"max_age": 39} and hist[0]["n_resultats"] == 97


def test_identical_search_later_is_not_duplicated(con):
    uid = create_user(con, "celia", "Radar-Demo-2026")
    log_search(con, uid, {"contrat": "Stage"}, 12, now=T0)
    log_search(con, uid, {"contrat": "Stage"}, 15, now=T0 + timedelta(hours=3))
    hist = list_searches(con, uid)
    assert len(hist) == 1 and hist[0]["n_resultats"] == 15
    assert hist[0]["created_at"] == T0 + timedelta(hours=3)


def test_history_is_capped(con):
    uid = create_user(con, "celia", "Radar-Demo-2026")
    for i in range(SEARCH_MAX_PER_USER + 5):
        log_search(con, uid, {"i": i}, i, now=T0 + timedelta(minutes=5 * i))
    hist = list_searches(con, uid, limit=1000)
    assert len(hist) == SEARCH_MAX_PER_USER
    assert hist[-1]["params"] == {"i": 5}  # les 5 plus anciennes ont été supprimées


def test_top_is_truncated(con):
    uid = create_user(con, "celia", "Radar-Demo-2026")
    log_search(con, uid, {}, 10, [f"E{i}" for i in range(10)], now=T0)
    assert len(list_searches(con, uid)[0]["top_resultats"]) == 5


def test_history_isolated_cleared_and_deleted_with_account(con):
    a = create_user(con, "celia", "Radar-Demo-2026")
    b = create_user(con, "mathis", "Autre-Compte-42")
    log_search(con, a, {"contrat": "Stage"}, 1, now=T0)
    log_search(con, b, {"contrat": "Emploi"}, 2, now=T0)
    assert [h["params"]["contrat"] for h in list_searches(con, b)] == ["Emploi"]
    clear_searches(con, b)
    assert list_searches(con, b) == [] and len(list_searches(con, a)) == 1
    delete_user(con, a)
    assert con.execute("SELECT count(*) FROM recherches").fetchone()[0] == 0


# --- Sécurité des mots de passe (D16) -----------------------------------------------------


@pytest.mark.parametrize(
    "password",
    [
        "Radar-Demo-2026",  # 4 types
        "radar demo 2026",  # phrase de passe : minuscules, chiffres, espaces = 3 types
    ],
)
def test_strong_passwords_accepted(password):
    assert password_problems(password, "celia") == []


@pytest.mark.parametrize(
    ("password", "fragment"),
    [
        ("Court-1", "12 caractères"),
        ("toutenminuscules", "types"),
        ("UnePhraseDePasse", "types"),  # minuscules + majuscules : 2 types
        ("123456789012", "types"),
        ("Motdepasse123", "courant"),
        ("AZERTY123456", "courant"),
        ("Celia-Radar-2026", "identifiant"),
        ("A1-" + "x" * 130, "au plus"),
    ],
)
def test_weak_passwords_rejected(password, fragment):
    problems = password_problems(password, "celia")
    assert any(fragment in p for p in problems), problems


def test_create_user_explains_refusal(con):
    with pytest.raises(AccountError, match="12 caractères"):
        create_user(con, "celia", "Court-1")


def test_account_locked_after_failures(con):
    uid = create_user(con, "celia", "Radar-Demo-2026")
    for i in range(LOGIN_MAX_FAILS):
        assert authenticate(con, "celia", "mauvais", now=T0 + timedelta(seconds=i)) is None
    # bloqué : même le bon mot de passe est refusé
    with pytest.raises(AccountLocked) as exc:
        authenticate(con, "celia", "Radar-Demo-2026", now=T0 + timedelta(minutes=1))
    assert exc.value.until > T0
    # débloqué après la durée
    later = T0 + LOGIN_LOCK_DURATION + timedelta(seconds=10)
    assert authenticate(con, "celia", "Radar-Demo-2026", now=later) == uid


def test_success_resets_failure_count(con):
    uid = create_user(con, "celia", "Radar-Demo-2026")
    for _ in range(LOGIN_MAX_FAILS - 1):
        authenticate(con, "celia", "mauvais", now=T0)
    assert authenticate(con, "celia", "Radar-Demo-2026", now=T0) == uid
    for _ in range(LOGIN_MAX_FAILS - 1):  # le compteur est reparti de zéro
        authenticate(con, "celia", "mauvais", now=T0)
    assert authenticate(con, "celia", "Radar-Demo-2026", now=T0) == uid


def test_unknown_user_never_locked(con):
    for _ in range(LOGIN_MAX_FAILS + 2):
        assert authenticate(con, "inconnu", "mauvais") is None


def test_old_database_is_migrated(tmp_path):
    import sqlite3

    path = tmp_path / "ancienne.db"
    old = sqlite3.connect(path)
    old.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE, "
        "password_hash TEXT NOT NULL, created_at TEXT NOT NULL)"
    )
    old.commit()
    old.close()
    c = connect(path)
    cols = {r[1] for r in c.execute("PRAGMA table_info(users)")}
    assert {"failed_logins", "locked_until"} <= cols
    c.close()
