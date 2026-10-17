"""Coder tests for U5/U7: predictions zip, its pre-write checks, and the rank -> zip chain."""

import importlib.util
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from ebnerd.eval.submission import write_predictions_zip

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
T0 = datetime(2023, 5, 18, 7, 0, 0)


def _script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_write_predictions_zip_format(tmp_path):
    path = tmp_path / "predictions.zip"
    write_predictions_zip([42, 0], [np.array([2, 1, 3]), [1]], path)
    with zipfile.ZipFile(path) as zf:
        assert zf.namelist() == ["predictions.txt"]
        text = zf.read("predictions.txt").decode()
    assert text == "42 [2,1,3]\n0 [1]\n"


ARTICLES = {
    "article_id": [10, 11, 12, 13, 14, 15],
    "total_inviews": [0] * 6,
    "total_pageviews": [0] * 6,
    "total_read_time": [0.0] * 6,
}
# Row 0: 11 newest, then 10 and 12 tied (input order). Row 1: 14, then the two unknowns.
INVIEW = [[10, 11, 12], [13, 14, 16], [15, 11]]
EXPECTED_RANKS = [[2, 1, 3], [2, 1, 3], [2, 1]]


@pytest.fixture
def data_root(tmp_path, monkeypatch):
    """A validation-shaped and a test-shaped split (STATE.md U7 (b)) over one articles file."""
    monkeypatch.setenv("EBNERD_DATA_ROOT", str(tmp_path))
    hour = timedelta(hours=1)
    # Article 13 has no published_time; article 16 is absent from the table: both rank last.
    published = [T0 + 2 * hour, T0 + 5 * hour, T0 + 2 * hour, None, T0, T0 + hour]
    (tmp_path / "raw").mkdir()
    pl.DataFrame({**ARTICLES, "published_time": published}).write_parquet(
        tmp_path / "raw" / "articles.parquet"
    )
    common = {
        "user_id": [100, 101, 100],
        "impression_time": [T0] * 3,
        "article_ids_inview": INVIEW,
        "device_type": [1, 2, 1],
        "session_id": [7, 8, 9],
        "is_sso_user": [False] * 3,
        "gender": [0, 1, None],
        "postcode": [1, None, 3],
        "age": [20, 30, 40],
        "is_subscriber": [False] * 3,
    }
    # Impression ids repeat 0 (like test beyond-accuracy rows); alignment is by row order.
    splits = {
        "validation": {
            "impression_id": [3, 0, 0],
            "article_ids_clicked": [[12], [14], [15, 15]],  # repeated click must count once
        },
        "test": {
            "impression_id": [5, 0, 0],
            "is_beyond_accuracy": [False, True, True],
            "read_time": [1.0, 2.0, 3.0],  # forbidden columns the loader must drop
            "scroll_percentage": [10.0, 20.0, 30.0],
        },
    }
    for split, extra in splits.items():
        (tmp_path / "raw" / split).mkdir()
        behaviors = tmp_path / "raw" / split / "behaviors.parquet"
        pl.DataFrame({**common, **extra}).write_parquet(behaviors)
    return tmp_path


def test_rank_recency_then_evaluate_then_zip(data_root, capsys, monkeypatch):
    ranks_path = data_root / "runs" / "recency" / "validation_ranks.parquet"
    _script("rank_recency").main(["--split", "validation", "--out", str(ranks_path)])

    ranks = pl.read_parquet(ranks_path)
    assert ranks.columns == ["impression_id", "ranks"]
    assert ranks["impression_id"].to_list() == [3, 0, 0]
    assert ranks["ranks"].to_list() == EXPECTED_RANKS

    # Slices of 2 and 1 rows: an unweighted mean of slice means would give auc 0.25, not 1/3.
    evaluate = _script("evaluate")
    monkeypatch.setattr(evaluate, "SLICE_ROWS", 2)
    evaluate.main(["--split", "validation", "--ranks", str(ranks_path)])
    out = dict(line.split("=") for line in capsys.readouterr().out.splitlines())
    # Positive ranks per impression: 3 of 3, 1 of 3, 2 of 2.
    assert float(out["auc"]) == pytest.approx((0 + 1 + 0) / 3)
    assert float(out["mrr"]) == pytest.approx((1 / 3 + 1 + 1 / 2) / 3)
    ndcg = (1 / np.log2(4) + 1 + 1 / np.log2(3)) / 3
    assert float(out["ndcg@5"]) == pytest.approx(ndcg)
    assert float(out["ndcg@10"]) == pytest.approx(ndcg)

    zip_path = data_root / "runs" / "recency" / "predictions.zip"
    _script("make_submission").main(
        ["--split", "validation", "--ranks", str(ranks_path), "--out", str(zip_path)]
    )
    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == ["predictions.txt"]
        assert zf.read("predictions.txt").decode() == "3 [2,1,3]\n0 [2,1,3]\n0 [2,1]\n"


def test_rank_recency_then_zip_on_test_schema(data_root):
    ranks_path = data_root / "runs" / "recency" / "test_ranks.parquet"
    _script("rank_recency").main(["--split", "test", "--out", str(ranks_path)])
    assert pl.read_parquet(ranks_path)["ranks"].to_list() == EXPECTED_RANKS

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        _script("evaluate").main(["--split", "test", "--ranks", str(ranks_path)])

    zip_path = data_root / "runs" / "recency" / "predictions.zip"
    _script("make_submission").main(
        ["--split", "test", "--ranks", str(ranks_path), "--out", str(zip_path)]
    )
    with zipfile.ZipFile(zip_path) as zf:
        assert zf.read("predictions.txt").decode() == "5 [2,1,3]\n0 [2,1,3]\n0 [2,1]\n"


def test_make_submission_rejects_non_permutation(data_root):
    ranks_path = data_root / "bad_ranks.parquet"
    broken = [[2, 1, 3], [2, 2, 3], [2, 1]]  # row 1 repeats a rank
    pl.DataFrame(
        {"impression_id": [5, 0, 0], "ranks": broken}, schema_overrides={"ranks": pl.List(pl.Int32)}
    ).write_parquet(ranks_path)
    zip_path = data_root / "predictions.zip"
    with pytest.raises(SystemExit, match="permutation"):
        _script("make_submission").main(
            ["--split", "test", "--ranks", str(ranks_path), "--out", str(zip_path)]
        )
    assert not zip_path.exists()
