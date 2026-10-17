"""Coder tests for U4; hand-computed and reference comparisons live in test_metrics_qa.py."""

import numpy as np

from ebnerd.eval.metrics import impression_metrics


def test_narrow_dtypes_give_same_result():
    group = np.array([3, 3, 3, 9, 9], dtype=np.int64)
    score = np.array([0.1, 0.9, 0.4, 0.3, 0.8], dtype=np.float64)
    label = np.array([1, 0, 0, 1, 0], dtype=np.int64)
    wide = impression_metrics(group, score, label)
    narrow = impression_metrics(
        group.astype(np.int32), score.astype(np.float32), label.astype(np.int8)
    )
    assert set(narrow) == {"auc", "mrr", "ndcg@5", "ndcg@10"}
    for k, v in wide.items():
        assert isinstance(narrow[k], float)
        assert narrow[k] == v
