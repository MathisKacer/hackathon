"""Administrateurs et gestion des comptes (T79), sur une base temporaire."""

import pytest

from radar import accounts, admin
from radar.accounts import AccountError

PWD = "Correct-Horse-42"


@pytest.fixture
def con(tmp_path):
    c = accounts.connect(tmp_path / "radar.db")
    admin.ensure_schema(c)
    return c


def _mk(con, name):
    return accounts.create_user(con, name, PWD)


def test_new_accounts_are_classic_and_only_the_script_promotes(con):
    uid = _mk(con, "maxence")
    assert not admin.is_admin(con, uid)
    admin.set_admin(con, "Maxence", True)
    assert admin.is_admin(con, uid)
    assert admin.list_log(con).iloc[0]["admin"] == admin.TERMINAL
    admin.set_admin(con, "maxence", False)
    assert not admin.is_admin(con, uid)
    with pytest.raises(AccountError, match="Aucun compte"):
        admin.set_admin(con, "inconnu", True)


def test_at_most_four_admins(con):
    for n in ("mathis", "celia", "maxence", "emma", "intrus"):
        _mk(con, n)
    for n in ("mathis", "celia", "maxence", "emma"):
        admin.set_admin(con, n, True)
    with pytest.raises(AccountError, match="Déjà 4"):
        admin.set_admin(con, "intrus", True)


def test_admin_actions_require_admin(con):
    a, u = _mk(con, "maxence"), _mk(con, "etudiant")
    with pytest.raises(AccountError, match="réservée"):
        admin.reset_password(con, a, u)  # pas encore administrateur
    with pytest.raises(AccountError, match="réservée"):
        admin.delete_account(con, u, a)


def test_unlock_reset_delete_classic_accounts(con):
    a, u = _mk(con, "maxence"), _mk(con, "etudiant")
    admin.set_admin(con, "maxence", True)
    # blocage après 5 échecs, puis déblocage par l'admin
    for _ in range(accounts.LOGIN_MAX_FAILS):
        accounts.authenticate(con, "etudiant", "mauvais")
    assert admin.list_users(con).set_index("username").loc["etudiant", "bloque"]
    admin.unlock(con, a, u)
    assert not admin.list_users(con).set_index("username").loc["etudiant", "bloque"]
    # mot de passe provisoire : valide, à changer, l'ancien ne marche plus
    temp = admin.reset_password(con, a, u)
    assert not accounts.password_problems(temp)
    assert accounts.authenticate(con, "etudiant", PWD) is None
    assert accounts.authenticate(con, "etudiant", temp) == u
    assert admin.must_change_password(con, u)
    admin.change_password(con, u, temp, "Nouveau-Mot-2-Passe")
    assert not admin.must_change_password(con, u)
    # suppression
    admin.delete_account(con, a, u)
    assert accounts.get_username(con, u) is None
    actions = admin.list_log(con)["action"].tolist()
    assert actions[:3] == ["compte supprimé", "mot de passe réinitialisé", "débloqué"]


def test_admins_cannot_reset_or_delete_other_admins_or_themselves(con):
    a, b = _mk(con, "maxence"), _mk(con, "celia")
    admin.set_admin(con, "maxence", True)
    admin.set_admin(con, "celia", True)
    with pytest.raises(AccountError, match="administrateur"):
        admin.reset_password(con, a, b)
    with pytest.raises(AccountError, match="administrateur"):
        admin.delete_account(con, a, b)
    with pytest.raises(AccountError, match="Mon espace"):
        admin.delete_account(con, a, a)
    admin.unlock(con, a, b)  # débloquer un autre admin reste possible


def test_change_password_rules(con):
    u = _mk(con, "etudiant")
    with pytest.raises(AccountError, match="actuel incorrect"):
        admin.change_password(con, u, "faux", "Nouveau-Mot-2-Passe")
    with pytest.raises(AccountError, match="refusé"):
        admin.change_password(con, u, PWD, "court")
    with pytest.raises(AccountError, match="différent"):
        admin.change_password(con, u, PWD, PWD)


def test_list_users_shows_counts_not_content(con):
    a = _mk(con, "maxence")
    accounts.save_search(con, a, "Rennes", {"ville": "Rennes (35000)"})
    users = admin.list_users(con)
    assert users.loc[0, "n_recherches"] == 1
    assert "params" not in users.columns and "ville" not in " ".join(users.columns)


def test_old_databases_get_the_new_columns(tmp_path):
    c = accounts.connect(tmp_path / "old.db")  # base sans les colonnes T79
    uid = accounts.create_user(c, "ancien", PWD)
    assert admin.is_admin(c, uid) is False  # ensure_schema appelé tout seul


def test_script(tmp_path, monkeypatch, capsys):
    import importlib.util

    monkeypatch.setattr(accounts, "DB_PATH", tmp_path / "radar.db")
    accounts.create_user(accounts.connect(), "maxence", PWD)
    spec = importlib.util.spec_from_file_location("admin_script", "scripts/admin.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main(["promouvoir", "maxence"]) == 0
    assert "est maintenant administrateur" in capsys.readouterr().out
    assert mod.main(["liste"]) == 0
    assert "ADMIN  maxence" in capsys.readouterr().out
    assert mod.main(["promouvoir", "personne"]) == 1
