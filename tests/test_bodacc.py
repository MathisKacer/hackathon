"""Tests de T23 : classement des jugements BODACC, situation par SIREN, pénalité et alerte."""

import json

import pandas as pd
import pytest

from radar.collect.bodacc import classify_nature, enrich_entreprises, procedures_by_siren
from radar.procedures import PENALTIES, alert_text, apply_procedures, penalty


@pytest.mark.parametrize(
    ("nature", "expected"),
    [
        ("Jugement d'ouverture de liquidation judiciaire", "liquidation"),
        ("Jugement de conversion en liquidation judiciaire", "liquidation"),
        ("Jugement de clôture pour insuffisance d'actif", "liquidation"),
        ("Jugement arrêtant un plan de cession", "liquidation"),
        (
            "Jugement prononçant la résolution du plan de redressement et la liquidation "
            "judiciaire",
            "liquidation",
        ),
        ("Jugement d'ouverture d'une procédure de redressement judiciaire", "redressement"),
        (
            "Jugement de conversion en redressement judiciaire de la procédure de sauvegarde",
            "redressement",
        ),
        ("Jugement d'ouverture d'une procédure de sauvegarde", "sauvegarde"),
        ("Jugement de plan de redressement", "plan"),
        ("Jugement arrêtant le plan de sauvegarde", "plan"),
        ("Jugement modifiant le plan de redressement", "plan"),
        ("Jugement de clôture pour extinction du passif", "fin"),
        ("Jugement mettant fin à la procédure de redressement judiciaire", "fin"),
        ("Jugement de clôture de la procédure de sauvegarde", "fin"),
        ("Rétractation de jugement d'ouverture sur tierce opposition", "fin"),
        ("Dépôt de l'état des créances", None),
        (
            "Liste des créances nées après le jugement d'ouverture d'une procédure de "
            "liquidation judiciaire",
            None,
        ),
        ("Jugement de faillite personnelle", None),
        ("Jugement d'interdiction de gérer", None),
        (None, None),
    ],
)
def test_classify_nature(nature, expected):
    assert classify_nature(nature) == expected


def _notice(i, siren, nature, date, typeavis="annonce"):
    return {
        "id": f"A{i:04d}",
        "dateparution": date,
        "typeavis": typeavis,
        "registre": f"{siren},{siren[:3]} {siren[3:6]} {siren[6:]}" if siren else None,
        "jugement": json.dumps({"nature": nature, "date": date}),
        "url_complete": f"https://www.bodacc.fr/x?q.id=id:A{i:04d}",
    }


RAW = pd.DataFrame(
    [
        # A : redressement puis liquidation → liquidation
        _notice(
            1,
            "111111111",
            "Jugement d'ouverture d'une procédure de redressement judiciaire",
            "2025-03-01",
        ),
        _notice(2, "111111111", "Jugement de conversion en liquidation judiciaire", "2025-09-01"),
        _notice(3, "111111111", "Dépôt de l'état des créances", "2026-01-01"),  # ignoré
        # B : redressement puis plan → plan
        _notice(
            4,
            "222222222",
            "Jugement d'ouverture d'une procédure de redressement judiciaire",
            "2025-01-10",
        ),
        _notice(5, "222222222", "Jugement de plan de redressement", "2025-12-10"),
        # C : sauvegarde puis fin → fin
        _notice(6, "333333333", "Jugement d'ouverture d'une procédure de sauvegarde", "2025-02-01"),
        _notice(7, "333333333", "Jugement mettant fin à la procédure de sauvegarde", "2026-02-01"),
        # D : annulation ignorée
        _notice(
            8,
            "444444444",
            "Jugement d'ouverture de liquidation judiciaire",
            "2026-05-01",
            typeavis="annulation",
        ),
        # Sans SIREN (entrepreneur au répertoire des métiers) : ignoré
        _notice(9, None, "Jugement d'ouverture de liquidation judiciaire", "2026-05-01"),
    ]
)


def test_procedures_by_siren_keeps_latest_relevant_event():
    p = procedures_by_siren(RAW).set_index("siren")
    assert p.loc["111111111", "procedure_type"] == "liquidation"
    assert p.loc["222222222", "procedure_type"] == "plan"
    assert p.loc["333333333", "procedure_type"] == "fin"
    assert "444444444" not in p.index
    assert len(p) == 3
    assert p.loc["111111111", "procedure_url"].endswith("A0002")


def test_enrich_entreprises_keeps_every_establishment():
    ent = pd.DataFrame(
        {
            "siret": [
                "11111111100011",
                "11111111100029",
                "22222222200022",
                "33333333300033",
                "55555555500055",
            ],
            "siren": ["111111111", "111111111", "222222222", "333333333", "555555555"],
            "procedure_collective": pd.array([pd.NA] * 5, dtype="boolean"),
        }
    )
    out = enrich_entreprises(ent, procedures_by_siren(RAW)).set_index("siret")
    assert len(out) == 5  # aucune entreprise supprimée
    assert out.loc["11111111100029", "procedure_type"] == "liquidation"  # tous les établissements
    assert out["procedure_collective"].tolist() == [True, True, True, False, False]
    assert pd.isna(out.loc["33333333300033", "procedure_type"])  # « fin » : plus d'alerte
    # relancer l'enrichissement ne duplique pas les colonnes
    again = enrich_entreprises(out.reset_index(), procedures_by_siren(RAW))
    assert list(again.columns).count("procedure_type") == 1


def test_penalty_depends_on_contract():
    assert penalty(None, "stage") == 1.0
    assert penalty("redressement", "alternance") < penalty("redressement", "stage") < 1
    assert penalty("liquidation", "stage") <= 0.1
    assert penalty("plan", "Emploi") == PENALTIES["plan"]["emploi"]  # casse ignorée
    assert penalty("sauvegarde", "inconnu") == PENALTIES["sauvegarde"]["tous"]


def test_alert_text():
    assert alert_text(None) == ""
    assert alert_text("fin") == ""
    txt = alert_text("redressement", "2026-03-15")
    assert txt.startswith("🟠") and "(depuis 03/2026)" in txt


def _orange():
    return pd.DataFrame(
        {
            "siret": ["1", "2", "3", "4"],
            "score": [0.8, 0.8, 0.8, 0.8],
            "procedure_type": [None, "sauvegarde", "redressement", "liquidation"],
            "procedure_date": [None, "2026-01-01", "2026-02-01", "2026-03-01"],
        }
    )


def test_apply_procedures_penalizes_and_hides_liquidation_by_default():
    out = apply_procedures(_orange(), "alternance")
    assert out["siret"].tolist() == ["1", "2", "3"]  # liquidation masquée
    assert out["score"].tolist() == pytest.approx([0.8, 0.8 * 0.75, 0.8 * 0.4])
    assert out["alerte"].iloc[0] == "" and out["alerte"].iloc[2].startswith("🟠")


def test_apply_procedures_can_show_liquidation():
    out = apply_procedures(_orange(), "stage", show_liquidation=True)
    assert len(out) == 4 and out["alerte"].iloc[3].startswith("🔴")


def test_apply_procedures_without_bodacc_columns_is_neutral():
    df = pd.DataFrame({"siret": ["1"], "score": [0.5]})
    out = apply_procedures(df, "stage")
    assert out["score"].tolist() == [0.5] and out["alerte"].tolist() == [""]
