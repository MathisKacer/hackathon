"""T34 — Métriques de validation (sans réseau, sans vraies données)."""

import numpy as np
import pandas as pd
import pytest

from radar.validation import auc, overlap_at_k, roc_points


def test_overlap_at_k():
    assert overlap_at_k(["a", "b", "c"], ["c", "b", "a"], k=3) == 1.0
    assert overlap_at_k(["a", "b"], ["c", "d"], k=2) == 0.0
    assert overlap_at_k(["a", "b", "c", "d"], ["a", "x", "b", "y"], k=2) == 0.5
    assert np.isnan(overlap_at_k([], ["a"]))


def test_auc_perfect_random_and_ties():
    y = pd.Series([0, 0, 1, 1])
    assert auc(pd.Series([1, 2, 3, 4]), y) == 1.0
    assert auc(pd.Series([4, 3, 2, 1]), y) == 0.0
    assert auc(pd.Series([1, 1, 1, 1]), y) == 0.5  # ex aequo : moitié
    rng = np.random.default_rng(0)
    s = pd.Series(rng.random(20_000))
    lab = pd.Series(rng.random(20_000) < 0.1)
    assert auc(s, lab) == pytest.approx(0.5, abs=0.02)


def test_auc_ignores_missing_scores_and_degenerate_labels():
    assert auc(pd.Series([1.0, np.nan, 3.0]), pd.Series([0, 1, 1])) == 1.0
    assert np.isnan(auc(pd.Series([1, 2]), pd.Series([1, 1])))


def test_roc_points_monotone():
    rng = np.random.default_rng(1)
    s = pd.Series(rng.random(1000))
    pts = roc_points(s, s > 0.7)
    assert pts[0] == (0.0, 0.0) and pts[-1][1] == pytest.approx(1.0)
    assert all(b[0] >= a[0] and b[1] >= a[1] for a, b in zip(pts, pts[1:], strict=False))
