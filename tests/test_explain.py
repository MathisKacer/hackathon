"""Tests de l'explication « Recommandée car … » (T32)."""

import pandas as pd

from radar.explain import add_explanations, explain


def _row(**kw):
    base = {
        "domaine": "data",
        "n_offres_domaine_siren": 0,
        "n_stage_domaine_siren": 0,
        "n_alternance_domaine_siren": 0,
        "c_intensite": 0.2,
        "c_embauche": 0.2,
        "c_embauche_source": "proxy_besoin_attendu",
        "naf_libelle": "Programmation informatique",
        "tranche_effectif": "12",
        "distance_km": 12.0,
        "couverture": 1.0,
    }
    return base | kw


def test_hidden_opportunity_comes_first_and_reads_well():
    txt = explain(_row(n_offres_domaine_siren=2, c_intensite=0.99, apport_c_intensite=0.5,
                       apport_c_cachee=0.1), "stage")  # fmt: skip
    assert txt.startswith("Recommandée car elle recrute des profils data (2 offres d'emploi")
    assert "aucune offre de stage" in txt
    assert "dont" not in txt  # pas de « 1 offre, dont 1 emploi »


def test_mixed_contracts_detail():
    txt = explain(_row(n_offres_domaine_siren=3, n_stage_domaine_siren=1), "alternance")
    assert "3 offres en ligne : 2 emplois, 1 stage" in txt


def test_lbb_and_sector_reasons():
    txt = explain(_row(c_embauche_source="la_bonne_boite", c_intensite=0.95), "stage")
    assert "La Bonne Boîte" in txt
    assert "son secteur (programmation informatique) recrute beaucoup" in txt


def test_order_follows_score_contributions():
    r = _row(c_intensite=0.9, c_embauche=0.95, distance_km=2.0,
             apport_c_proximite=0.6, apport_c_intensite=0.1, apport_c_embauche=0.05)  # fmt: skip
    txt = explain(r, "stage")
    assert txt.index("2,0 km") < txt.index("secteur") < txt.index("établissement")


def test_caveat_when_region_not_collected_and_fallback():
    assert "pas encore collectées" in explain(_row(couverture=0.0), "stage")
    assert explain(_row(), "stage").startswith("Recommandée d'après le besoin estimé")


def test_add_explanations_limits_rows():
    df = pd.DataFrame([_row(c_intensite=0.9)] * 5)
    out = add_explanations(df, "stage", limit=3)
    assert out["explication"].notna().sum() == 3 and out["explication"].iloc[3] is None
    assert add_explanations(df.head(0), "stage").empty


def test_external_signals_are_not_crowded_out():
    """Recruteur LBA et La Bonne Boîte passent avant les raisons statistiques (rang centile)."""
    r = _row(n_offres_domaine_siren=4, recruteur_lba=True, c_intensite=0.99, c_embauche=0.97,
             apport_c_intensite=0.3, apport_c_embauche=0.29, apport_c_recruteur_lba=0.2,
             apport_c_cachee=0.1)  # fmt: skip
    txt = explain(r, "alternance")
    assert "La bonne alternance la repère comme recruteur" in txt
    assert txt.index("aucune offre d'alternance") < txt.index("La bonne alternance")
