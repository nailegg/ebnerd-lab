"""QA tests for U4 official metrics (STATE.md "U4 공식 지표 명세").

Written from the spec only; the Coder implementation is not consulted.
The reference implementation below is deliberately slow and literal: one
Python loop per impression, O(n^2) pairwise AUC, explicit stable sort.
"""

import math

import numpy as np
import pytest
from ebnerd.eval.metrics import impression_metrics

KEYS = ("auc", "mrr", "ndcg@5", "ndcg@10")
TOL = 1e-9


# --------------------------------------------------------------------------
# Reference implementation (slow, literal transcription of the spec)
# --------------------------------------------------------------------------


def _ranks(scores: list[float]) -> list[int]:
    """1-based rank of each candidate: score descending, ties keep input order."""
    order = sorted(range(len(scores)), key=lambda i: -scores[i])  # sorted() is stable
    ranks = [0] * len(scores)
    for position, i in enumerate(order):
        ranks[i] = position + 1
    return ranks


def _auc(scores: list[float], labels: list[int]) -> float:
    pos = [s for s, y in zip(scores, labels, strict=True) if y == 1]
    neg = [s for s, y in zip(scores, labels, strict=True) if y == 0]
    total = 0.0
    for p in pos:
        for n in neg:
            if p > n:
                total += 1.0
            elif p == n:
                total += 0.5
    return total / (len(pos) * len(neg))


def _mrr(scores: list[float], labels: list[int]) -> float:
    ranks = _ranks(scores)
    total = 0.0
    n_pos = 0
    for r, y in zip(ranks, labels, strict=True):
        if y == 1:
            total += 1.0 / r
            n_pos += 1
    return total / n_pos


def _dcg(labels_in_rank_order: list[int], k: int) -> float:
    total = 0.0
    for position, y in enumerate(labels_in_rank_order[:k]):
        rank = position + 1
        total += (2**y - 1) / math.log2(rank + 1)
    return total


def _ndcg(scores: list[float], labels: list[int], k: int) -> float:
    ranks = _ranks(scores)
    by_rank = [0] * len(labels)
    for r, y in zip(ranks, labels, strict=True):
        by_rank[r - 1] = y
    ideal = sorted(labels, reverse=True)
    return _dcg(by_rank, k) / _dcg(ideal, k)


def reference_metrics(group: np.ndarray, score: np.ndarray, label: np.ndarray) -> dict[str, float]:
    """Per-impression metrics averaged over impressions (contiguous group blocks)."""
    sums = dict.fromkeys(KEYS, 0.0)
    n_impressions = 0
    i = 0
    n = len(group)
    while i < n:
        j = i
        while j < n and group[j] == group[i]:
            j += 1
        scores = [float(s) for s in score[i:j]]
        labels = [int(y) for y in label[i:j]]
        sums["auc"] += _auc(scores, labels)
        sums["mrr"] += _mrr(scores, labels)
        sums["ndcg@5"] += _ndcg(scores, labels, 5)
        sums["ndcg@10"] += _ndcg(scores, labels, 10)
        n_impressions += 1
        i = j
    return {k: sums[k] / n_impressions for k in KEYS}


# --------------------------------------------------------------------------
# Hand-computed cases
# --------------------------------------------------------------------------

LOG2_3 = math.log2(3)

# Case A: 2 candidates, positive scored highest. Everything is 1.0.
CASE_A = {
    "score": [0.2, 0.9],
    "label": [0, 1],
    "expected": {"auc": 1.0, "mrr": 1.0, "ndcg@5": 1.0, "ndcg@10": 1.0},
}

# Case B: 5 candidates, three-way tie at 0.5 including a negative in front.
# Stable descending order: idx0(0.5,neg) idx1(0.5,pos) idx3(0.5,pos) idx2(0.3,neg) idx4(0.1,neg)
# -> positives at ranks 2 and 3.
# AUC: each positive vs negatives {0.5, 0.3, 0.1} = 0.5 + 1 + 1 = 2.5; (2.5 + 2.5) / 6.
# MRR: (1/2 + 1/3) / 2.
# DCG@5 = 1/log2(3) + 1/log2(4); ideal = 1/log2(2) + 1/log2(3).
_B_DCG = 1 / LOG2_3 + 1 / 2
_B_IDEAL = 1 + 1 / LOG2_3
CASE_B = {
    "score": [0.5, 0.5, 0.3, 0.5, 0.1],
    "label": [0, 1, 0, 1, 0],
    "expected": {
        "auc": 5 / 6,
        "mrr": (1 / 2 + 1 / 3) / 2,
        "ndcg@5": _B_DCG / _B_IDEAL,
        "ndcg@10": _B_DCG / _B_IDEAL,
    },
}

# Case C: 12 candidates, no ties, rank = 13 - score. Positives at ranks 1 and 7,
# so nDCG@5 (only rank 1 counts) differs from nDCG@10 (ranks 1 and 7 count).
# AUC: rank-1 positive beats 10 negatives, rank-7 positive beats 5 -> 15/20.
# MRR: (1 + 1/7) / 2.
# DCG@5 = 1; DCG@10 = 1 + 1/log2(8) = 1 + 1/3; ideal = 1 + 1/log2(3).
_C_IDEAL = 1 + 1 / LOG2_3
CASE_C = {
    "score": [3, 12, 6, 1, 9, 11, 7, 2, 10, 4, 8, 5],
    "label": [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "expected": {
        "auc": 15 / 20,
        "mrr": (1 + 1 / 7) / 2,
        "ndcg@5": 1 / _C_IDEAL,
        "ndcg@10": (1 + 1 / 3) / _C_IDEAL,
    },
}

HAND_CASES = {"A": CASE_A, "B": CASE_B, "C": CASE_C}


def _arrays(case: dict, group_id: int = 0):
    n = len(case["score"])
    return (
        np.full(n, group_id, dtype=np.int64),
        np.asarray(case["score"], dtype=np.float64),
        np.asarray(case["label"], dtype=np.int64),
    )


def _assert_close(result: dict[str, float], expected: dict[str, float]) -> None:
    assert set(result) == set(KEYS)
    for k in KEYS:
        assert isinstance(result[k], float), k
        assert result[k] == pytest.approx(expected[k], abs=TOL), k


# --------------------------------------------------------------------------
# Reference self-consistency (does not touch the implementation under test)
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name", list(HAND_CASES))
def test_reference_matches_hand_values(name):
    case = HAND_CASES[name]
    _assert_close(reference_metrics(*_arrays(case)), case["expected"])


def test_reference_perfect_ranking_single_positive_is_one():
    n = 12
    score = np.arange(n, 0, -1, dtype=np.float64)  # strictly descending
    label = np.array([1] + [0] * (n - 1), dtype=np.int64)
    group = np.zeros(n, dtype=np.int64)
    for v in reference_metrics(group, score, label).values():
        assert v == pytest.approx(1.0, abs=TOL)


def test_reference_perfect_ranking_multi_positive():
    # With several positives the spec's MRR (mean of 1/rank over positives) is < 1
    # even for a perfect ranking; AUC and nDCG are still 1.
    n = 12
    score = np.arange(n, 0, -1, dtype=np.float64)
    label = np.array([1, 1, 1] + [0] * (n - 3), dtype=np.int64)
    group = np.zeros(n, dtype=np.int64)
    result = reference_metrics(group, score, label)
    assert result["auc"] == pytest.approx(1.0, abs=TOL)
    assert result["ndcg@5"] == pytest.approx(1.0, abs=TOL)
    assert result["ndcg@10"] == pytest.approx(1.0, abs=TOL)
    assert result["mrr"] == pytest.approx((1 + 1 / 2 + 1 / 3) / 3, abs=TOL)


def test_reference_reversed_ranking_has_auc_zero():
    n = 8
    score = np.arange(n, 0, -1, dtype=np.float64)
    label = np.array([0] * 5 + [1] * 3, dtype=np.int64)  # all positives ranked last
    group = np.zeros(n, dtype=np.int64)
    result = reference_metrics(group, score, label)
    assert result["auc"] == pytest.approx(0.0, abs=TOL)
    # positives at ranks 6, 7, 8
    assert result["mrr"] == pytest.approx((1 / 6 + 1 / 7 + 1 / 8) / 3, abs=TOL)
    assert result["ndcg@5"] == pytest.approx(0.0, abs=TOL)
    ideal = 1 + 1 / LOG2_3 + 1 / 2
    assert result["ndcg@10"] == pytest.approx(
        (1 / math.log2(7) + 1 / 3 + 1 / math.log2(9)) / ideal, abs=TOL
    )


def test_reference_tie_keeps_input_order():
    group = np.zeros(2, dtype=np.int64)
    score = np.array([0.5, 0.5])
    # positive first in input -> rank 1
    r = reference_metrics(group, score, np.array([1, 0]))
    assert r["auc"] == pytest.approx(0.5, abs=TOL)
    assert r["mrr"] == pytest.approx(1.0, abs=TOL)
    assert r["ndcg@5"] == pytest.approx(1.0, abs=TOL)
    # positive second in input -> rank 2
    r = reference_metrics(group, score, np.array([0, 1]))
    assert r["auc"] == pytest.approx(0.5, abs=TOL)
    assert r["mrr"] == pytest.approx(0.5, abs=TOL)
    assert r["ndcg@5"] == pytest.approx(1 / LOG2_3, abs=TOL)


# --------------------------------------------------------------------------
# Tests of the implementation under test
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name", list(HAND_CASES))
def test_hand_case_single_impression(name):
    case = HAND_CASES[name]
    _assert_close(impression_metrics(*_arrays(case)), case["expected"])


def test_hand_cases_combined_are_averaged():
    parts = [_arrays(HAND_CASES[name], group_id=i) for i, name in enumerate(HAND_CASES)]
    group = np.concatenate([p[0] for p in parts])
    score = np.concatenate([p[1] for p in parts])
    label = np.concatenate([p[2] for p in parts])
    expected = {
        k: sum(c["expected"][k] for c in HAND_CASES.values()) / len(HAND_CASES) for k in KEYS
    }
    _assert_close(impression_metrics(group, score, label), expected)


def test_tie_keeps_input_order():
    group = np.zeros(2, dtype=np.int64)
    score = np.array([0.5, 0.5])
    _assert_close(
        impression_metrics(group, score, np.array([1, 0])),
        {"auc": 0.5, "mrr": 1.0, "ndcg@5": 1.0, "ndcg@10": 1.0},
    )
    _assert_close(
        impression_metrics(group, score, np.array([0, 1])),
        {"auc": 0.5, "mrr": 0.5, "ndcg@5": 1 / LOG2_3, "ndcg@10": 1 / LOG2_3},
    )


def test_noncontiguous_group_ids():
    # groups 7 (3 candidates) and 42 (2 candidates); ids are neither 0-based nor consecutive
    group = np.array([7, 7, 7, 42, 42], dtype=np.int64)
    score = np.array([0.1, 0.9, 0.4, 0.3, 0.8])
    label = np.array([1, 0, 0, 1, 0], dtype=np.int64)
    # group 7: positive at rank 3 of 3 -> auc 0, mrr 1/3, ndcg 1/log2(4) = 1/2
    # group 42: positive at rank 2 of 2 -> auc 0, mrr 1/2, ndcg 1/log2(3)
    expected = {
        "auc": 0.0,
        "mrr": (1 / 3 + 1 / 2) / 2,
        "ndcg@5": (1 / 2 + 1 / LOG2_3) / 2,
        "ndcg@10": (1 / 2 + 1 / LOG2_3) / 2,
    }
    _assert_close(impression_metrics(group, score, label), expected)
    _assert_close(reference_metrics(group, score, label), expected)


def _random_case(seed: int, n_impressions: int = 200):
    rng = np.random.default_rng(seed)
    groups, scores, labels = [], [], []
    # non-contiguous, increasing group ids with random gaps
    gid = int(rng.integers(1, 1000))
    for _ in range(n_impressions):
        n = int(rng.integers(2, 31))  # 2..30 candidates
        # quantize scores to a handful of levels so ties are frequent
        s = rng.choice([0.0, 0.25, 0.5, 0.75, 1.0], size=n)
        y = rng.integers(0, 2, size=n)
        # guarantee at least one positive and one negative
        y[int(rng.integers(0, n))] = 1
        candidates = np.flatnonzero(y == 1)
        if len(candidates) == n:
            y[int(rng.choice(candidates))] = 0
        groups.append(np.full(n, gid, dtype=np.int64))
        scores.append(s.astype(np.float64))
        labels.append(y.astype(np.int64))
        gid += int(rng.integers(1, 50))
    return np.concatenate(groups), np.concatenate(scores), np.concatenate(labels)


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_random_matches_reference(seed):
    group, score, label = _random_case(seed)
    assert len(np.unique(group)) == 200
    assert 2 <= np.bincount(group).max() <= 30
    _assert_close(impression_metrics(group, score, label), reference_metrics(group, score, label))
