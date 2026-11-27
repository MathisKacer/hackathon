"""Suggesteur de ville (T55), sans réseau."""

import pandas as pd
import requests

from radar.communes import communes_from_companies, load_communes, parse_communes, place_of

PAYLOAD = [
    {
        "nom": "Rennes",
        "code": "35238",
        "codesPostaux": ["35000", "35200"],
        "centre": {"type": "Point", "coordinates": [-1.6884, 48.1159]},
        "population": 230890,
    },
    {
        "nom": "Bruz",
        "code": "35047",
        "codesPostaux": ["35170"],
        "centre": {"type": "Point", "coordinates": [-1.7454, 48.0247]},
        "population": 18000,
    },
    {"nom": "Sans centre", "code": "99999", "codesPostaux": ["99999"], "population": 5},
    # homonymes partageant un code postal → libellés rendus uniques
    {"nom": "Moûtiers", "code": "1", "codesPostaux": ["73600"], "centre": {"coordinates": [6, 45]}},
    {"nom": "Moûtiers", "code": "2", "codesPostaux": ["73600"], "centre": {"coordinates": [7, 46]}},
]


def test_parse_communes():
    df = parse_communes(PAYLOAD)
    # une ligne par commune, tous ses codes postaux entre parenthèses
    assert df["label"].tolist()[:2] == ["Rennes (35000, 35200)", "Bruz (35170)"]
    assert "Sans centre (99999)" not in set(df["label"])
    assert df["label"].is_unique
    assert {"Moûtiers (73600) · 1", "Moûtiers (73600) · 2"} <= set(df["label"])


def test_place_of():
    df = parse_communes(PAYLOAD)
    p = place_of("Bruz (35170)", df)
    assert (round(p.lat, 4), round(p.lon, 4), p.label) == (48.0247, -1.7454, "Bruz (35170)")
    assert place_of(None, df) is None
    assert place_of("Atlantide (00000)", df) is None


class _Down:
    def get(self, *a, **k):
        raise requests.ConnectionError("hors ligne")


def test_offline_fallback_on_companies(tmp_path, monkeypatch):
    ent = pd.DataFrame(
        {
            "commune": ["RENNES", "RENNES", "BRUZ"],
            "code_postal": ["35000", "35200", "35170"],
            "lat": [48.10, 48.12, 48.02],
            "lon": [-1.68, -1.70, -1.74],
        }
    )
    path = tmp_path / "entreprises.parquet"
    ent.to_parquet(path)
    df = communes_from_companies(path)
    assert df["label"].tolist() == ["Rennes (35000, 35200)", "Bruz (35170)"]
    assert df.loc[0, "lat"] == 48.11
    monkeypatch.setitem(__import__("radar.config").config.FILES, "entreprises", path)
    offline = load_communes(session=_Down())["label"].tolist()
    assert offline == ["Rennes (35000, 35200)", "Bruz (35170)"]
