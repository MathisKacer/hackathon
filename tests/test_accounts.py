"""Tests des comptes facultatifs (T48). Base SQLite temporaire, jamais data/app/radar.db."""

import pytest

from radar.accounts import (
    AccountError,
    authenticate,
    connect,
    create_user,
    delete_user,
    get_username,
    hash_password,
    load_profile,
    save_profile,
    verify_password,
)


@pytest.fixture
def con(tmp_path):
    c = connect(tmp_path / "radar.db")
    yield c
    c.close()


def test_password_hash_is_salted_and_verifiable():
    h1, h2 = hash_password("motdepasse1"), hash_password("motdepasse1")
    assert h1 != h2  # sel aléatoire
    assert "motdepasse1" not in h1
    assert verify_password("motdepasse1", h1)
    assert not verify_password("mauvais", h1)
    assert not verify_password("motdepasse1", "pas-un-hache")


def test_create_and_authenticate(con):
    uid = create_user(con, "  Celia ", "motdepasse1")
    assert get_username(con, uid) == "celia"  # identifiant normalisé
    assert authenticate(con, "CELIA", "motdepasse1") == uid
    assert authenticate(con, "celia", "mauvais") is None
    assert authenticate(con, "inconnu", "motdepasse1") is None


def test_password_never_stored_in_clear(con):
    create_user(con, "celia", "motdepasse1")
    stored = con.execute("SELECT password_hash FROM users").fetchone()[0]
    assert "motdepasse1" not in stored and stored.startswith("scrypt$")


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("ab", "motdepasse1"),
        ("nom avec espace", "motdepasse1"),
        ("x" * 31, "motdepasse1"),
        ("celia", "court"),
        ("celia", "x" * 129),
    ],
)
def test_invalid_credentials_rejected(con, username, password):
    with pytest.raises(AccountError):
        create_user(con, username, password)


def test_duplicate_username_rejected(con):
    create_user(con, "celia", "motdepasse1")
    with pytest.raises(AccountError, match="déjà pris"):
        create_user(con, "CELIA", "autremotdepasse")


def test_profile_roundtrip_and_update(con):
    uid = create_user(con, "celia", "motdepasse1")
    assert load_profile(con, uid) == {}
    save_profile(con, uid, {"contrat": "Stage", "regions": ["Bretagne"], "max_age": 30})
    assert load_profile(con, uid) == {"contrat": "Stage", "regions": ["Bretagne"], "max_age": 30}
    save_profile(con, uid, {"contrat": "Alternance"})
    assert load_profile(con, uid) == {"contrat": "Alternance"}


def test_profile_size_limit(con):
    uid = create_user(con, "celia", "motdepasse1")
    with pytest.raises(AccountError):
        save_profile(con, uid, {"x": "a" * 20_000})


def test_profiles_are_isolated(con):
    a = create_user(con, "celia", "motdepasse1")
    b = create_user(con, "mathis", "motdepasse2")
    save_profile(con, a, {"contrat": "Stage"})
    assert load_profile(con, b) == {}


def test_delete_user_removes_profile(con):
    uid = create_user(con, "celia", "motdepasse1")
    save_profile(con, uid, {"contrat": "Stage"})
    delete_user(con, uid)
    assert get_username(con, uid) is None
    assert authenticate(con, "celia", "motdepasse1") is None
    assert con.execute("SELECT count(*) FROM profils").fetchone()[0] == 0
    create_user(con, "celia", "nouveaumdp1")  # l'identifiant redevient libre
