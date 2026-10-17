"""Rank every impression's candidates by `published_time`, newest first (STATE.md U5)."""

import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
import polars as pl

from ebnerd.prepare.load import load_articles, load_behaviors

# Candidates with unknown `published_time` rank last: fill with a date older than any article.
OLDEST = datetime(1900, 1, 1)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    behaviors = load_behaviors(args.split).select("impression_id", "article_ids_inview")
    articles = load_articles().select("article_id", "published_time")

    # Long format in candidate order; `row` is the behaviors row number.
    candidates = (
        behaviors.select(pl.col("article_ids_inview").alias("article_id"))
        .with_row_index("row")
        .explode("article_id")
        .join(articles, on="article_id", how="left")
        .select("row", pl.col("published_time").fill_null(OLDEST))
    )
    del articles

    # Stable order by (row, newest first); rank = offset from the row's first candidate.
    order = candidates.select(
        pl.arg_sort_by(["row", "published_time"], descending=[False, True], maintain_order=True)
    ).to_series()
    lens = behaviors["article_ids_inview"].list.len()
    starts = (lens.cum_sum() - lens).gather(candidates["row"].gather(order)).to_numpy()
    ranks = np.empty(order.len(), dtype=np.int32)
    ranks[order.to_numpy()] = np.arange(order.len(), dtype=np.int32) - starts + 1
    del order, starts

    folded = (
        pl.DataFrame({"row": candidates["row"], "ranks": ranks})
        .group_by("row", maintain_order=True)
        .agg("ranks")
    )
    del candidates, ranks

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out = pl.DataFrame({"impression_id": behaviors["impression_id"], "ranks": folded["ranks"]})
    out.write_parquet(args.out)


if __name__ == "__main__":
    main()
