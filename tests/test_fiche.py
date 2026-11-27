"""Tests de la fiche entreprise (T43), sur de petits fichiers temporaires."""

import json

import pandas as pd

from radar.fiche import bodacc_history, company_offers, evidence, links, load_company


def test_load_company(tmp_path):
    p = tmp_path / "entreprises.parquet"
    pd.DataFrame(
        {"siret": ["11111111100011", "22222222200022"], "nom": ["ACME", "BETA"], "lat": [48.1, 0]}
    ).to_parquet(p)
    assert load_company("11111111100011", p)["nom"] == "ACME"
    assert load_company("99999999999999", p) is None
    assert load_company("11111111100011", tmp_path / "absent.parquet") is None


def test_company_offers_by_siren_or_source_siret_without_intermediaries(tmp_path):
    p = tmp_path / "offres.parquet"
    pd.DataFrame(
        {
            "titre": ["Data analyst", "Stage data", "Alternance BI", "Autre entreprise", "Intérim"],
            "contrat": ["emploi", "stage", "alternance", "stage", "emploi"],
            "domaine": ["data"] * 5,
            "commune": ["Rennes"] * 5,
            "source": ["adzuna", "adzuna", "lba", "adzuna", "adzuna"],
            "url": [f"https://ex.org/{i}" for i in range(5)],
            "date_publication": [
                "2026-11-01",
                "2026-11-20",
                "2026-10-01",
                "2026-11-25",
                "2026-11-26",
            ],
            "siren_match": ["111111111", "111111111", None, "222222222", "111111111"],
            "siret": [None, None, "11111111100029", None, None],
            "intermediaire": [False, False, False, False, True],
        }
    ).to_parquet(p)
    out = company_offers("111111111", "11111111100029", p)
    assert out["titre"].tolist() == ["Stage data", "Data analyst", "Alternance BI"]  # récentes
    assert company_offers(None, None, p).empty
    assert company_offers("111111111", None, tmp_path / "absent.parquet").empty


def test_bodacc_history(tmp_path):
    p = tmp_path / "bodacc.parquet"

    def notice(siren, nature, date, typeavis="annonce"):
        return {
            "dateparution": date,
            "typeavis": typeavis,
            "registre": f"{siren},{siren[:3]} {siren[3:6]} {siren[6:]}",
            "jugement": json.dumps({"nature": nature, "date": date}),
            "url_complete": f"https://www.bodacc.fr/x/{siren}/{date}",
        }

    pd.DataFrame(
        [
            notice(
                "111111111",
                "Jugement d'ouverture d'une procédure de redressement judiciaire",
                "2025-03-01",
            ),
            notice("111111111", "Jugement de plan de redressement", "2026-01-15"),
            notice("111111111", "Dépôt de l'état des créances", "2025-06-01"),
            notice(
                "111111111",
                "Jugement d'ouverture de liquidation judiciaire",
                "2026-05-01",
                "annulation",
            ),
            notice("222222222", "Jugement d'ouverture de liquidation judiciaire", "2026-02-01"),
        ]
    ).to_parquet(p)
    h = bodacc_history("111111111", p)
    assert h["situation"].tolist() == ["plan", "autre", "redressement"]  # récentes d'abord
    assert h["url"].iloc[0].endswith("2026-01-15")
    assert bodacc_history("333333333", p).empty
    assert bodacc_history("111111111", tmp_path / "absent.parquet").empty


def test_evidence_levels():
    assert (
        evidence(pd.Series({"n_offres_domaine_siren": 7, "couverture": 1.0}))["niveau"] == "élevé"
    )
    assert evidence(pd.Series({"n_offres_domaine": 1}))["niveau"] == "moyen"
    assert evidence(pd.Series({"n_offres_domaine": 0}))["niveau"] == "faible"
    e = evidence(pd.Series({"n_offres_domaine_siren": 3, "couverture": 0.0}))
    assert e["niveau"] == "non collecté"
    full = evidence(
        pd.Series(
            {
                "n_offres_domaine_siren": 2,
                "n_stage_domaine_siren": 1,
                "intensite_post": 1.5,
                "intensite_ic_bas": 0.4,
                "intensite_ic_haut": 3.1,
                "prior_moyenne": 0.6,
            }
        )
    )
    assert (full["n_stage"], full["intensite"], full["ic_haut"]) == (1, 1.5, 3.1)


def test_links():
    row = pd.Series(
        {"siret": "11111111100011", "lat": 48.11, "lon": -1.68, "procedure_url": "https://b/1"}
    )
    out = links(row)
    assert out["Annuaire des entreprises"].endswith("/11111111100011")
    assert "mlat=48.11000" in out["Carte (OpenStreetMap)"]
    assert out["Annonce BODACC"] == "https://b/1"
    assert set(links(pd.Series({"siret": "1", "lat": None, "lon": None}))) == {
        "Annuaire des entreprises"
    }


# --- Affichage (app/fiche_ui.py), avec AppTest ---------------------------------------------


def _mini_app():
    import sys
    from pathlib import Path

    import pandas as pd

    sys.path.insert(0, str(Path.cwd() / "app"))
    from fiche_ui import render_fiche

    render_fiche(
        pd.DataFrame(
            {
                "siret": ["11111111100011", "22222222200022"],
                "siren": ["111111111", "222222222"],
                "nom": ["ACME", "BETA"],
                "commune": ["RENNES", "BRUZ"],
                "score": [0.8, 0.3],
                "distance_km": [1.2, 8.5],
                "c_intensite": [0.9, 0.4],
                "apport_c_intensite": [0.8, 0.3],
                "n_offres_domaine_siren": [3, 0],
                "intensite_post": [1.5, 0.2],
                "intensite_ic_bas": [0.5, 0.0],
                "intensite_ic_haut": [3.0, 0.9],
                "prior_moyenne": [0.6, 0.6],
                "alerte": ["", "🟠 En redressement judiciaire (depuis 03/2026)"],
                "coef_procedure": [1.0, 0.4],
                "explication": ["Recommandée car elle publie 3 offres data.", None],
                "lat": [48.11, 48.02],
                "lon": [-1.68, -1.75],
            }
        )
    )


def test_render_fiche(monkeypatch):
    import streamlit as st
    from streamlit.testing.v1 import AppTest

    from radar import fiche

    monkeypatch.setattr(
        fiche,
        "load_company",
        lambda siret: pd.Series(
            {
                "siret": siret,
                "siren": siret[:9],
                "nom": "ACME",
                "naf_libelle": "Programmation",
                "tranche_libelle": "20 à 49 salariés",
                "categorie": "PME",
                "siege": True,
                "adresse": "1 RUE DU TEST",
                "code_postal": "35000",
                "commune": "RENNES",
                "diffusion_partielle": False,
            }
        ),
    )
    monkeypatch.setattr(
        fiche,
        "company_offers",
        lambda siren, siret: pd.DataFrame(
            {
                "date_publication": ["2026-11-20"],
                "titre": ["Stage data"],
                "contrat": ["stage"],
                "domaine": ["data"],
                "commune": ["Rennes"],
                "source": ["adzuna"],
                "url": ["https://ex.org/1"],
            }
        ),
    )
    monkeypatch.setattr(
        fiche,
        "bodacc_history",
        lambda siren: pd.DataFrame(columns=["date", "situation", "nature", "url"]),
    )
    st.cache_data.clear()
    at = AppTest.from_function(_mini_app, default_timeout=30)
    at.run()
    assert not at.exception
    md = [m.value for m in at.markdown]
    assert "### ACME" in md
    assert any("Recommandée car" in i.value for i in at.info)  # colonne T32
    assert any(m.startswith("Niveau de preuve") and "moyen" in m for m in md)
    assert any("intervalle crédible à 90 %" in m for m in md)
    assert any("1 RUE DU TEST" in m for m in md)
    assert any("Stage data" in d.value.to_string() for d in at.dataframe)

    at.session_state["fiche_siret"] = "22222222200022"  # entreprise avec alerte
    at.run()
    assert not at.exception
    assert any("redressement" in w.value for w in at.warning)
    st.cache_data.clear()
