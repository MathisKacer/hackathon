"""T6 — Dictionnaire des domaines (radar/domains.yaml) et règle de classement."""

import re

import pytest

from radar.domains import OTHER, classify, default_domain, load_domains

ROME_CODE = re.compile(r"^[A-N]\d{4}$")


def test_file_is_well_formed():
    domains = load_domains()
    assert list(domains)[0] == "data"  # data first: it wins ties
    assert default_domain() in domains
    assert OTHER not in domains
    for d in domains.values():
        assert d.label and d.keywords is not None
        for code in [*d.rome, *d.rome_partial]:
            assert ROME_CODE.match(code), code
        assert not set(d.rome) & set(d.rome_partial)


def test_each_rome_code_in_a_single_domain():
    seen: dict[str, str] = {}
    for d in load_domains().values():
        for code in d.rome:
            assert code not in seen, f"{code} dans {seen.get(code)} et {d.key}"
            seen[code] = d.key


def test_fake_data_uses_the_same_domains():
    from radar.fake_data import DOMAINS

    assert tuple(load_domains()) == DOMAINS


@pytest.mark.parametrize(
    "title,expected",
    [
        # Titres « data » de tests/test_quick_filter.py (filtre v0 de Mathis) : même verdict.
        ("Data Analyst H/F", "data"),
        ("Stage - Data Scientist", "data"),
        ("Ingénieur statisticien", "data"),
        ("Chargé d'études statistiques", "data"),
        ("Alternance Business Intelligence", "data"),
        ("Consultant Power BI", "data"),
        ("Analyste de données", "data"),
        ("Machine Learning Engineer", "data"),
        ("Ingénieur IA générative", "data"),
        ("Actuaire", "data"),
        ("Biostatisticien", "data"),
        # Autres domaines
        ("Développeur Python full-stack", "informatique"),
        ("Ingénieur DevOps", "informatique"),
        ("Ingénieur Réseaux, WiFi & Téléphonie H/F", "informatique"),
        ("Contrôleur de gestion H/F", "finance"),
        ("Stage - Analyste financier", "finance"),
        ("Accounting Generalist", OTHER),  # anglais non couvert : assumé, T13 pourra compléter
        ("Chargé de communication", "marketing"),
        ("Alternance Chef de produit marketing digital", "marketing"),
        ("Chargé de recrutement", "rh"),
        ("Gestionnaire paie", "rh"),
        # Pièges
        ("Technicien Datacenter", "informatique"),  # « data » exclu, mais c'est de l'informatique
        ("Délégué à la protection des données (DPO)", OTHER),
        ("Opérateur de saisie de données", OTHER),
        ("Responsable biologie", OTHER),  # « bi » ne doit pas matcher dans un mot
        ("Commercial terrain", OTHER),
        (None, OTHER),
    ],
)
def test_classify_title_only(title, expected):
    assert classify(title) == expected


def test_classify_with_rome_code():
    assert classify("Chargé d'études", "M1430") == "marketing"  # code ambigu, pas de mot data
    assert classify("Chargé d'études data marketing", "M1430") == "data"  # code ambigu + data
    assert classify("Consultant", "M1405") == "data"  # code sûr, même sans mot-clé
    assert classify("Data engineer", "M1805") == "informatique"  # le code sûr prime sur le titre
    assert classify("Alternance", "M1419,M1405") == "data"  # plusieurs codes (La bonne alternance)
    assert classify("Assistant RH", "Z9999") == "rh"  # code inconnu → titre
