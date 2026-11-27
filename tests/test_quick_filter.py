import pandas as pd
import pytest

from radar.process.quick_filter import contract_from_title, is_data_title, prepare_offers


@pytest.mark.parametrize(
    "title",
    [
        "Data Analyst H/F",
        "Stage - Data Scientist",
        "Ingénieur statisticien",
        "Chargé d'études statistiques",
        "Alternance Business Intelligence",
        "Consultant Power BI",
        "Analyste de données",
        "Machine Learning Engineer",
        "Ingénieur IA générative",
        "Actuaire",
        "Biostatisticien",
    ],
)
def test_data_titles_detected(title):
    assert is_data_title(title)


@pytest.mark.parametrize(
    "title",
    [
        "Accounting Generalist",
        "Ingénieur Réseaux, WiFi & Téléphonie H/F",
        "FPGA Engineering Lead",
        "Chargé.e de mission Extraction / Phytochimie",
        "Responsable biologie",  # « bi » ne doit pas matcher dans un mot
        "Commercial terrain",
        None,
    ],
)
def test_non_data_titles_rejected(title):
    assert not is_data_title(title)


@pytest.mark.parametrize(
    "title,expected",
    [
        ("Stage - Data Analyst", "stage"),
        ("Stagiaire data scientist", "stage"),
        ("Data Science Internship", "stage"),
        ("Alternance Data Engineer", "alternance"),
        ("Apprenti(e) statisticien", "alternance"),
        ("Data Engineer en contrat de professionnalisation", "alternance"),
        ("Data Engineer Senior", "emploi"),
        (None, "emploi"),
    ],
)
def test_contract_from_title(title, expected):
    assert contract_from_title(title) == expected


def test_prepare_offers_drops_ungeolocated_and_adds_columns():
    df = pd.DataFrame(
        {
            "titre": ["Stage Data Analyst", "Comptable"],
            "lat": [48.1, None],
            "lon": [-1.6, None],
            "date_publication": ["2026-11-20T10:00:00Z", "2026-11-20T10:00:00Z"],
        }
    )
    out = prepare_offers(df)
    assert len(out) == 1
    assert out.iloc[0][["is_data", "contrat"]].tolist() == [True, "stage"]
    assert out.iloc[0]["age_jours"] >= 0
