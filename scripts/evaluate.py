"""Score a ranks parquet against a split's labels with the four official metrics (STATE.md U5)."""

import argparse
from pathlib import Path

import polars as pl

from ebnerd.eval.metrics import KEYS, impression_metrics
from ebnerd.prepare.load import load_behaviors, load_labels

# Behaviors rows per slice; the long format of a full split does not fit the 15 GB VM.
SLICE_ROWS = 1_000_000


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", required=True)
    parser.add_argument("--ranks", required=True, type=Path)
    args = parser.parse_args(argv)

    ranks = pl.read_parquet(args.ranks).get_column("ranks")
    clicked = load_labels(args.split).get_column("article_ids_clicked")
    inview = load_behaviors(args.split).get_column("article_ids_inview")
    if ranks.len() != clicked.len():
        raise SystemExit(f"row count mismatch: ranks {ranks.len()}, labels {clicked.len()}")

    # Metrics are impression means, so slice means weighted by impression count are exact.
    totals = dict.fromkeys(KEYS, 0.0)
    for start in range(0, ranks.len(), SLICE_ROWS):
        rows = pl.DataFrame(
            {
                "article_id": inview.slice(start, SLICE_ROWS),
                "rank": ranks.slice(start, SLICE_ROWS),
                "clicked": clicked.slice(start, SLICE_ROWS),
            }
        ).with_row_index("row")
        # Clicks exploded on their own and joined back, so the clicked list is never replicated.
        # Clicked lists can repeat an article; deduplicate so no candidate row is doubled.
        clicks = (
            rows.select("row", pl.col("clicked").list.unique().alias("article_id"))
            .explode("article_id")
            .with_columns(label=pl.lit(1, dtype=pl.Int8))
        )
        long = (
            rows.select("row", "article_id", "rank")
            .explode("article_id", "rank")
            .join(clicks, on=["row", "article_id"], how="left", maintain_order="left")
            .select(
                "row",
                (-pl.col("rank")).cast(pl.Int32).alias("score"),
                pl.col("label").fill_null(0),
            )
        )
        metrics = impression_metrics(
            long["row"].to_numpy(), long["score"].to_numpy(), long["label"].to_numpy()
        )
        for key in KEYS:
            totals[key] += metrics[key] * rows.height

    for key in KEYS:
        print(f"{key}={totals[key] / ranks.len()}")


if __name__ == "__main__":
    main()
