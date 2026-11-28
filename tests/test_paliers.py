"""Paliers de priorité du score orange (T65), règle mixte."""

import numpy as np
import pandas as pd

from radar.paliers import TIERS, add_tiers, assign_tiers, rule_text, tier_color, tier_text


def test_tiers_are_ordered():
    assert [t.rank for t in TIERS] == [1, 2, 3, 4]
    assert all(a.top_share < b.top_share for a, b in zip(TIERS, TIERS[1:], strict=False))
    assert all(a.min_score > b.min_score for a, b in zip(TIERS, TIERS[1:], strict=False))


def test_uniform_scores_follow_shares():
    s = pd.Series(np.linspace(1, 0.61, 100))  # tous au-dessus des minima : seul le rang compte
    counts = assign_tiers(s).value_counts().sort_index().tolist()
    assert counts == [10, 20, 30, 40]


def test_floor_blocks_weak_searches():
    s = pd.Series([0.5, 0.4, 0.3, 0.2, 0.1] * 4)  # meilleure = 0,5 < 0,60
    t = assign_tiers(s)
    assert 1 not in set(t)
    assert t[s == 0.5].eq(2).all()  # dans les 30 % et ≥ 0,45


def test_best_one_is_prioritaire_even_in_small_results():
    assert assign_tiers(pd.Series([0.9, 0.5, 0.2])).tolist() == [1, 3, 4]


def test_ties_are_treated_together_and_prudently():
    t = assign_tiers(pd.Series([0.8] * 10))  # tous ex æquo : aucun ne monte grâce à l'égalité
    assert t.nunique() == 1 and t.iloc[0] == 4


def test_add_tiers_and_texts():
    df = add_tiers(pd.DataFrame({"score": [0.9, 0.1]}))
    assert df["palier"].tolist() == [1, 4]
    assert df["palier_libelle"].tolist() == ["●●● Cible prioritaire", "○○○ Moins indiquée"]
    assert add_tiers(pd.DataFrame()).empty
    assert tier_text(2, with_dots=False) == "Bonne cible"
    assert tier_text(np.nan) == ""
    assert tier_color(np.nan) == TIERS[-1].color
    assert "10 %" in rule_text() and "0,60" in rule_text()


def test_score_gradient_goes_from_light_to_dark():
    from radar.paliers import SCORE_GRADIENT, score_color, text_color_on

    assert score_color(0) == SCORE_GRADIENT[0][1] and score_color(1) == SCORE_GRADIENT[-1][1]
    assert score_color(0.75) == "#e8590c"

    def lum(c):
        return sum(w * int(c[i : i + 2], 16) for w, i in ((0.299, 1), (0.587, 3), (0.114, 5)))

    lums = [lum(score_color(x / 10)) for x in range(11)]
    assert all(a > b for a, b in zip(lums, lums[1:], strict=False))  # de plus en plus foncé
    assert score_color(np.nan) == TIERS[-1].color
    assert (
        text_color_on(score_color(0.1)) == "#111111" and text_color_on(score_color(1)) == "#ffffff"
    )


def test_need_floor_is_absolute():
    """D47 : sans besoin attendu suffisant, même la meilleure n'est pas « prioritaire »."""
    s = pd.Series(np.linspace(1, 0.61, 100))
    weak = assign_tiers(s, pd.Series(0.0, index=s.index))
    assert set(weak) == {4}
    need = pd.Series([0.5] * 5 + [0.06] * 5 + [0.0] * 90)  # 5 fortes, 5 moyennes
    t = assign_tiers(s, need)
    assert t.iloc[:5].eq(1).all() and t.iloc[5:10].eq(2).all() and t.iloc[10:].eq(4).all()
    df = add_tiers(pd.DataFrame({"score": [0.9, 0.8], "besoin_attendu": [0.01, 0.3]}))
    assert df["palier"].tolist() == [3, 3]  # 0,9 manque de besoin ; 0,8 pas dans les 10 %
    assert "besoin attendu" in rule_text()


def test_map_keeps_best_tiers_first():
    import sys

    sys.path.insert(0, "app")
    from carte import MIN_SPONTANEOUS_ON_MAP, spontaneous_on_map

    df = pd.DataFrame({"palier": [4, 4, 2, 1, 3] + [4] * 50})
    assert spontaneous_on_map(df)["palier"].tolist()[:2] == [1, 2]
    weak = pd.DataFrame({"palier": [4] * 50})
    assert len(spontaneous_on_map(weak)) == MIN_SPONTANEOUS_ON_MAP  # jamais de carte vide
