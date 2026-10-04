"""Read rows from a CSV file."""

from __future__ import annotations

import csv
from pathlib import Path

from sluice.context import Row, RunContext
from sluice.errors import StepError

NAME = "read_csv"
DESCRIPTION = "Read rows from a CSV file on disk."


def run(rows: list[Row], options: dict, ctx: RunContext) -> list[Row]:
    path = options.get("path")
    if not path:
        raise StepError(
            "no 'path' given", step=NAME, hint='add  path = "pipelines/data/customers.csv"'
        )

    source = Path(path)
    if not source.exists():
        raise StepError(
            f"{source} does not exist",
            step=NAME,
            hint="paths are relative to where you ran sluice from",
        )

    encoding = options.get("encoding", "utf-8")
    delimiter = options.get("delimiter", ",")

    out: list[Row] = []
    with source.open(newline="", encoding=encoding) as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        if reader.fieldnames is None:
            raise StepError(
                f"{source} is empty", step=NAME, hint="a CSV needs at least a header row"
            )
        for i, record in enumerate(reader, start=2):  # line 1 is the header
            out.append(dict(record))
            ctx.count("rows_read")
            if i % 50_000 == 0:
                ctx.debug(f"read {i:,} lines")

    ctx.debug(f"{source}: {len(out)} rows, columns {reader.fieldnames}")
    return out
