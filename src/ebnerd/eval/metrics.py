"""Impression-level AUC, MRR, nDCG@5, nDCG@10 averaged over impressions (STATE.md U4).

Definitions follow ebnerd-benchmark: candidates sorted by score descending, ties keep
input order; AUC counts tied positive-negative pairs as 0.5; MRR averages 1/rank over
positives; nDCG@k uses gain 2^label - 1 and discount 1/log2(rank + 1).
"""

import numpy as np

KEYS = ("auc", "mrr", "ndcg@5", "ndcg@10")


def _idcg_table(k: int) -> np.ndarray:
    """ideal DCG@k for 0..k positives: cumulative discounted gain of the top ranks."""
    ranks = np.arange(1, k + 1)
    return np.concatenate([[0.0], np.cumsum(1.0 / np.log2(ranks + 1))])


def impression_metrics(group: np.ndarray, score: np.ndarray, label: np.ndarray) -> dict[str, float]:
    """Long format; rows of the same impression (`group`) form a contiguous block.

    Every impression is assumed to contain at least one positive and one negative.
    All work is vectorised over positives, so memory stays within a few arrays of
    the input length.
    """
    group = np.asarray(group)
    score = np.asarray(score)
    label = np.asarray(label) != 0
    n = group.shape[0]

    # Stable sort: group ascending, score descending, ties keep input order.
    order = np.lexsort((-score, group))
    group = group[order]
    score = score[order]
    label = label[order]
    del order

    new_group = group[1:] != group[:-1]
    starts = np.concatenate([[0], np.flatnonzero(new_group) + 1])
    size = np.diff(starts, append=n)
    n_imp = starts.shape[0]

    # Tie runs: rows with equal (group, score) are contiguous after the sort.
    run_starts = np.concatenate([[0], np.flatnonzero(new_group | (score[1:] != score[:-1])) + 1])
    run_ends = np.diff(run_starts, append=n) + run_starts - 1
    del new_group, group, score

    # Positives only: their impression, 1-based rank, and tie-averaged rank.
    pos = np.flatnonzero(label)
    imp = np.searchsorted(starts, pos, side="right") - 1
    rank = pos - starts[imp] + 1
    run = np.searchsorted(run_starts, pos, side="right") - 1
    avg_rank = (run_starts[run] + run_ends[run]) / 2.0 - starts[imp] + 1.0

    n_pos = np.bincount(imp, minlength=n_imp).astype(np.float64)
    n_neg = size - n_pos

    # AUC via Mann-Whitney U on ascending (score) tie-averaged ranks.
    asc_rank_sum = np.bincount(imp, weights=size[imp] + 1.0 - avg_rank, minlength=n_imp)
    auc = (asc_rank_sum - n_pos * (n_pos + 1.0) / 2.0) / (n_pos * n_neg)

    mrr = np.bincount(imp, weights=1.0 / rank, minlength=n_imp) / n_pos

    discount = 1.0 / np.log2(rank + 1.0)
    result = {"auc": float(auc.mean()), "mrr": float(mrr.mean())}
    for k in (5, 10):
        dcg = np.bincount(imp, weights=discount * (rank <= k), minlength=n_imp)
        idcg = _idcg_table(k)[np.minimum(n_pos, k).astype(np.int64)]
        result[f"ndcg@{k}"] = float((dcg / idcg).mean())
    return result
