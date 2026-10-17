from datetime import datetime

import polars as pl
import pytest

from ebnerd.prepare.load import (
    BEHAVIOR_COLUMNS,
    load_article_vectors,
    load_articles,
    load_behaviors,
    load_history,
    load_labels,
)

T0 = datetime(2023, 5, 18, 7, 0, 0)


def _behaviors_base() -> dict:
    # Forbidden columns are included on purpose; the loader must drop them.
    return {
        "impression_id": [3, 1, 2],
        "impression_time": [T0, T0, T0],
        "read_time": [1.0, 2.0, 3.0],
        "scroll_percentage": [10.0, None, 30.0],
        "device_type": [1, 2, 1],
        "article_ids_inview": [[10, 11], [12], [13, 14, 15]],
        "user_id": [100, 101, 100],
        "is_sso_user": [True, False, False],
        "gender": [0, 1, None],
        "postcode": [1, None, 3],
        "age": [20, 30, 40],
        "is_subscriber": [False, True, False],
        "session_id": [7, 8, 9],
    }


@pytest.fixture
def data_root(tmp_path, monkeypatch):
    monkeypatch.setenv("EBNERD_DATA_ROOT", str(tmp_path))
    raw = tmp_path / "raw"
    (raw / "train").mkdir(parents=True)
    (raw / "test").mkdir()

    train = _behaviors_base()
    train["article_id"] = [50, None, 51]
    train["article_ids_clicked"] = [[11], [12], [13, 15]]
    train["next_read_time"] = [4.0, 5.0, 6.0]
    train["next_scroll_percentage"] = [40.0, 50.0, 60.0]
    pl.DataFrame(train).write_parquet(raw / "train" / "behaviors.parquet")

    test = _behaviors_base()
    test["is_beyond_accuracy"] = [False, True, False]
    pl.DataFrame(test).write_parquet(raw / "test" / "behaviors.parquet")

    history = pl.DataFrame(
        {
            "user_id": [100, 101],
            "impression_time_fixed": [[T0, T0], [T0]],
            "scroll_percentage_fixed": [[1.0, 2.0], [3.0]],
            "article_id_fixed": [[10, 11], [12]],
            "read_time_fixed": [[5.0, 6.0], [7.0]],
        }
    )
    history.write_parquet(raw / "train" / "history.parquet")

    pl.DataFrame(
        {
            "article_id": [10, 11],
            "title": ["a", "b"],
            "published_time": [T0, None],
            "category": [1, 2],
            "total_inviews": [5, 6],
            "total_pageviews": [1, 2],
            "total_read_time": [1.5, 2.5],
        }
    ).write_parquet(raw / "articles.parquet")

    pl.DataFrame(
        {"article_id": [10, 11], "contrastive_vector": [[0.1, 0.2], [0.3, 0.4]]}
    ).write_parquet(raw / "contrastive_vector.parquet")
    return raw


@pytest.mark.parametrize(
    ("split", "expected_ba"),
    [("train", [False, False, False]), ("test", [False, True, False])],
)
def test_load_behaviors_columns_and_order(data_root, split, expected_ba):
    df = load_behaviors(split)
    assert df.columns == BEHAVIOR_COLUMNS
    assert df["impression_id"].to_list() == [3, 1, 2]
    assert df["is_beyond_accuracy"].to_list() == expected_ba
    assert df["is_beyond_accuracy"].dtype == pl.Boolean


def test_load_labels_train(data_root):
    df = load_labels("train")
    assert df.columns == ["impression_id", "article_ids_clicked"]
    assert df["impression_id"].to_list() == [3, 1, 2]
    assert df["article_ids_clicked"].to_list() == [[11], [12], [13, 15]]


def test_load_labels_test_raises(data_root):
    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        load_labels("test")


def test_load_history_as_is(data_root):
    df = load_history("train")
    assert df.equals(pl.read_parquet(data_root / "train" / "history.parquet"))


def test_load_articles_drops_aggregates(data_root):
    df = load_articles()
    assert df.columns == ["article_id", "title", "published_time", "category"]
    assert df["article_id"].to_list() == [10, 11]


def test_load_article_vectors_as_is(data_root):
    df = load_article_vectors()
    assert df.equals(pl.read_parquet(data_root / "contrastive_vector.parquet"))
