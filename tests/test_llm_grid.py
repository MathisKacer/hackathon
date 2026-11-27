"""Tests de la grille secteur × taille × domaine (T77), avec un faux LLM (aucun appel réseau)."""

import json

import pandas as pd
import pytest

from radar.score import llm_grid as g


def _answer(note=2):
    return {
        "grille": {s: dict.fromkeys(g.DOMAINS, note) for s in g.SIZE_KEYS},
        "justification": {d: "parce que" for d in g.DOMAINS},
    }


class FakeClient:
    model = "faux:1b"

    def __init__(self, replies):
        self.replies, self.calls = list(replies), 0

    def complete(self, prompt):
        assert "62.02A" in prompt and "Conseil en systèmes" in prompt  # consigne remplie
        self.calls += 1
        return self.replies.pop(0)


@pytest.fixture(autouse=True)
def _tmp_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(g, "CACHE_DIR", tmp_path)


def test_validate_rejects_bad_shapes():
    g.validate(_answer())
    bad = _answer()
    bad["grille"]["10-49"]["data"] = 4
    with pytest.raises(ValueError):
        g.validate(bad)
    bad = _answer()
    del bad["grille"]["1000+"]
    with pytest.raises(ValueError):
        g.validate(bad)
    ok = _answer()
    ok["grille"]["10-49"]["rh"] = "1"  # chaîne numérique acceptée
    assert g.validate(ok)["grille"]["10-49"]["rh"] == 1


def test_retry_then_cache():
    lib = "Conseil en systèmes et logiciels informatiques"
    client = FakeClient(["pas du json", "```json\n" + json.dumps(_answer(3)) + "\n```"])
    res = g.rate_naf(client, "62.02A", lib)
    assert res["grille"]["1000+"]["data"] == 3 and client.calls == 2
    again = g.rate_naf(client, "62.02A", lib)  # depuis le cache : pas d'appel
    assert again == res and client.calls == 2


def test_naf_table_and_long_format():
    ent = pd.DataFrame(
        {
            "siret": ["1", "2", "3"],
            "naf": ["62.02A", "62.02A", "10.71C"],
            "naf_libelle": ["Conseil", "Conseil", "Boulangerie"],
            "tranche_effectif": ["11", "42", "12"],
        }
    )
    t = g.naf_table(ent).set_index("naf")
    assert t.loc["62.02A", "n_etab"] == 2 and t.loc["62.02A", "n_1000+"] == 1
    res = _answer() | {"naf": "62.02A", "naf_libelle": "Conseil", "modele": "m", "consigne": "v1"}
    long = g.to_long([res])
    assert len(long) == 4 * 5 and set(long["taille"]) == set(g.SIZE_KEYS.values())
    assert g.size_class(pd.Series(["42", "00"])).tolist()[0] == "1 000 et plus"
