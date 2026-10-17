"""Turn a ranks parquet into the Codabench predictions zip (STATE.md U5, D6)."""

import argparse
from pathlib import Path

import polars as pl

from ebnerd.eval.submission import write_predictions_zip


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranks", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    df = pl.read_parquet(args.ranks)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # iter_rows converts list cells in buffered slices; iterating the Series directly would not.
    ranks = (row for (row,) in df.select("ranks").iter_rows())
    write_predictions_zip(df["impression_id"], ranks, args.out)


if __name__ == "__main__":
    main()
