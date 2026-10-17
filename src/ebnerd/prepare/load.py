"""Read one split's raw parquet files, keeping only columns allowed by AGENTS.md section 2."""

import os
from pathlib import Path

import polars as pl

BEHAVIOR_COLUMNS = [
    "impression_id",
    "user_id",
    "impression_time",
    "article_ids_inview",
    "device_type",
    "session_id",
    "is_sso_user",
    "gender",
    "postcode",
    "age",
    "is_subscriber",
    "is_beyond_accuracy",
]
LABEL_COLUMNS = ["impression_id", "article_ids_clicked"]
ARTICLE_AGGREGATE_COLUMNS = ["total_inviews", "total_pageviews", "total_read_time"]


def _raw_dir() -> Path:
    return Path(os.environ["EBNERD_DATA_ROOT"]) / "raw"


def load_behaviors(split: str) -> pl.DataFrame:
    lf = pl.scan_parquet(_raw_dir() / split / "behaviors.parquet")
    if "is_beyond_accuracy" not in lf.collect_schema().names():
        lf = lf.with_columns(pl.lit(False).alias("is_beyond_accuracy"))
    return lf.select(BEHAVIOR_COLUMNS).collect()


def load_labels(split: str) -> pl.DataFrame:
    return pl.scan_parquet(_raw_dir() / split / "behaviors.parquet").select(LABEL_COLUMNS).collect()


def load_history(split: str) -> pl.DataFrame:
    return pl.read_parquet(_raw_dir() / split / "history.parquet")


def load_articles() -> pl.DataFrame:
    lf = pl.scan_parquet(_raw_dir() / "articles.parquet")
    return lf.drop(ARTICLE_AGGREGATE_COLUMNS).collect()


def load_article_vectors() -> pl.DataFrame:
    return pl.read_parquet(_raw_dir() / "contrastive_vector.parquet")
