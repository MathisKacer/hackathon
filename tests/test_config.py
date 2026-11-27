from radar.config import FILES, PATHS, settings


def test_paths_exist():
    assert PATHS.processed.exists()
    assert FILES["entreprises"].parent == PATHS.processed


def test_settings_repr_hides_secrets():
    assert "renseignées" in repr(settings)
