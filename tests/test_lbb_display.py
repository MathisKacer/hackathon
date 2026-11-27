"""T29 — Affichage de La Bonne Boîte dans la couche orange (D27)."""

import pandas as pd

from radar.spontaneous import COMPONENTS, LBB_SOURCE, signaled_by_lbb


def test_signaled_by_lbb():
    df = pd.DataFrame({"c_embauche_source": [LBB_SOURCE, "proxy_besoin_attendu", None]})
    assert signaled_by_lbb(df).tolist() == [True, False, False]


def test_signaled_by_lbb_without_column():
    """Scores d'avant T28 ou données factices : aucune mention, pas d'erreur."""
    df = pd.DataFrame({"siret": ["1", "2"]})
    assert not signaled_by_lbb(df).any()


def test_c_embauche_label_mentions_la_bonne_boite():
    label, help_ = COMPONENTS["c_embauche"]
    assert label == "Potentiel d'embauche"
    assert "La Bonne Boîte" in help_
