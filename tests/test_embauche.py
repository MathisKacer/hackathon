"""T28 — La Bonne Boîte (collecteur) et composante c_embauche, sans réseau."""

import numpy as np
import pandas as pd

from radar.collect import lbb
from radar.score.embauche import SOURCE_LBB, SOURCE_PROXY, embauche_component


def _s():
    return pd.DataFrame(
        {
            "siret": ["A", "B", "C", "D", "E"],
            "besoin_attendu": [5.0, 1.0, 0.0, 9.0, 3.0],
        }
    )


def test_without_lbb_keeps_proxy_order():
    out = embauche_component(_s(), None)
    assert (out["c_embauche_source"] == SOURCE_PROXY).all()
    assert out.sort_values("c_embauche")["siret"].tolist() == ["C", "B", "E", "A", "D"]
    assert out["c_embauche"].between(0, 1).all()


def test_lbb_establishments_rank_first_then_by_potential():
    best = pd.DataFrame({"siret": ["B", "C"], "lbb_potentiel": [10.0, 40.0]})
    out = embauche_component(_s(), best).set_index("siret")
    # B et C (listés par LBB) passent devant tous les autres, même D au plus fort proxy
    assert out.loc[["B", "C"], "c_embauche"].min() > out.loc[["A", "D", "E"], "c_embauche"].max()
    assert out.loc["C", "c_embauche"] > out.loc["B", "c_embauche"]  # 40 > 10
    assert out.loc["D", "c_embauche"] > out.loc["A", "c_embauche"]  # proxy conservé dessous
    assert out.loc["C", "c_embauche"] == 1.0
    assert out.loc["B", "c_embauche_source"] == SOURCE_LBB
    assert out.loc["A", "c_embauche_source"] == SOURCE_PROXY
    assert np.isnan(out.loc["A", "lbb_potentiel"])


def test_lbb_unknown_sirets_change_nothing():
    best = pd.DataFrame({"siret": ["ZZZ"], "lbb_potentiel": [99.0]})
    a = embauche_component(_s(), best)
    b = embauche_component(_s(), None)
    assert a["c_embauche"].equals(b["c_embauche"])


ITEM = {
    "rome": "M1811",
    "siret": "43975281700205",
    "email": "yes",
    "company_name": "ASTEK FRANCE",
    "naf": "6202A",
    "naf_label": "Conseil en systèmes et logiciels informatiques",
    "location": {"lat": 48.13, "lon": -1.64},
    "city": "Rennes",
    "postcode": "35700",
    "department_number": "35",
    "region": "Bretagne",
    "hiring_potential": 35.2,
    "is_high_potential": False,
}


def test_item_to_row():
    row = lbb.item_to_row(ITEM, "data", "t")
    assert list(row) == lbb.COLUMNS
    assert row["naf"] == "62.02A"  # même format que SIRENE
    assert row["lbb_potentiel"] == 35.2 and row["lat"] == 48.13
    assert "email" not in row  # simple drapeau oui/non, non conservé


class FakeClient:
    """Bretagne : 150 résultats sur 2 pages ; les autres régions : rien."""

    real_calls = 0

    def __init__(self):
        self.calls = []

    def search(self, romes, region, page=1):
        self.calls.append((region, page))
        if region != "Bretagne":
            return {"hits": 0, "items": []}
        n = 100 if page == 1 else 50
        items = [dict(ITEM, siret=f"{page}{i:013d}", hiring_potential=float(i)) for i in range(n)]
        return {"hits": 150, "items": items}


def test_collect_paginates_and_deduplicates():
    client = FakeClient()
    df = lbb.collect("data", client=client)
    assert len(df) == 150 and df["siret"].is_unique
    assert ("Bretagne", 2) in client.calls and ("Bretagne", 3) not in client.calls
    best = lbb.best_by_siret(pd.concat([df, df.assign(rome="M1405", lbb_potentiel=999.0)]), "data")
    assert len(best) == 150 and (best["lbb_potentiel"] == 999.0).all()  # max sur les métiers
