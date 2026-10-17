"""The Codabench predictions zip (STATE.md U5, D6)."""

import io
import zipfile
from collections.abc import Iterable
from pathlib import Path


def write_predictions_zip(
    impression_ids: Iterable[int], ranks: Iterable[Iterable[int]], path: Path
) -> None:
    """Write a zip holding only `predictions.txt`.

    One line per row: `<impression_id> [r1,r2,...]` (no spaces inside the brackets).
    """
    with (
        zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf,
        zf.open("predictions.txt", "w") as raw,
        io.TextIOWrapper(raw, encoding="utf-8", newline="\n") as f,
    ):
        for impression_id, row in zip(impression_ids, ranks, strict=True):
            f.write(f"{impression_id} [{','.join(map(str, row))}]\n")
