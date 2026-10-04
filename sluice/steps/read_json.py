"""Read rows from a JSON file holding a list of objects."""

from __future__ import annotations

import json
from pathlib import Path

from sluice.context import Row, RunContext
from sluice.errors import StepError

NAME = "read_json"
DESCRIPTION = "Read rows from a JSON file containing a list of objects."


def run(rows: list[Row], options: dict, ctx: RunContext) -> list[Row]:
    path = options.get("path")
    if not path:
        raise StepError("no 'path' given", step=NAME)

    source = Path(path)
    if not source.exists():
        raise StepError(f"{source} does not exist", step=NAME)

    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StepError(
            f"{source} is not valid JSON: {exc}",
            step=NAME,
            hint=f"line {exc.lineno}, column {exc.colno}",
        ) from exc

    if isinstance(data, dict):
        key = options.get("key")
        if not key:
            raise StepError(
                f"{source} holds an object, not a list",
                step=NAME,
                hint='say which key holds the list, e.g.  key = "records"',
            )
        data = data.get(key)
        if data is None:
            raise StepError(f"{source} has no key '{key}'", step=NAME)

    if not isinstance(data, list):
        raise StepError(f"{source} does not contain a list", step=NAME)

    out: list[Row] = []
    for i, record in enumerate(data, start=1):
        if not isinstance(record, dict):
            raise StepError(
                f"item {i} is a {type(record).__name__}, not an object", step=NAME, row=i
            )
        out.append(dict(record))
        ctx.count("rows_read")
    return out
