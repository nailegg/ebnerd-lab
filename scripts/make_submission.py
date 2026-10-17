"""Turn a ranks parquet into the Codabench predictions zip (STATE.md U5, D6).

Before writing, the ranks are checked against the split's behaviors (STATE.md U7).
"""

import argparse
from pathlib import Path

import polars as pl

from ebnerd.eval.submission import write_predictions_zip
from ebnerd.prepare.load import load_behaviors


def check_ranks(ranks: pl.DataFrame, behaviors: pl.DataFrame) -> None:
    """Raise SystemExit naming the first failed check; return silently if all pass."""
    if ranks.height != behaviors.height:
        raise SystemExit(f"row count mismatch: ranks {ranks.height}, behaviors {behaviors.height}")
    if not ranks["impression_id"].equals(behaviors["impression_id"]):
        raise SystemExit("impression_id mismatch: ranks and behaviors differ in values or order")
    if not ranks["ranks"].list.len().equals(behaviors["article_ids_inview"].list.len()):
        raise SystemExit("ranks length mismatch: some row's ranks differ in length from its inview")
    n = pl.col("ranks").list.len()
    expected = pl.int_ranges(1, n + 1, dtype=ranks.schema["ranks"].inner)
    if not ranks.select((pl.col("ranks").list.sort() == expected).all()).item():
        raise SystemExit("ranks permutation mismatch: some row's ranks are not a 1..n permutation")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", required=True)
    parser.add_argument("--ranks", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    df = pl.read_parquet(args.ranks)
    check_ranks(df, load_behaviors(args.split).select("impression_id", "article_ids_inview"))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    # iter_rows converts list cells in buffered slices; iterating the Series directly would not.
    ranks = (row for (row,) in df.select("ranks").iter_rows())
    write_predictions_zip(df["impression_id"], ranks, args.out)


if __name__ == "__main__":
    main()
