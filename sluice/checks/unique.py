"""Fail if a column repeats a value."""

from __future__ import annotations

from sluice.context import Row, RunContext
from sluice.errors import ConfigError

NAME = "unique"
DESCRIPTION = "Fail if a column contains the same value twice."


def check(rows: list[Row], options: dict, ctx: RunContext) -> list[str]:
    column = options.get("column")
    if not column:
        raise ConfigError(f"{NAME} needs 'column'", hint='column = "customer_id"')

    seen: dict[str, int] = {}
    problems: list[str] = []
    for i, row in enumerate(rows, start=1):
        if column not in row:
            problems.append(f"row {i}: no column '{column}'")
            continue
        value = str(row[column])
        if value in seen:
            problems.append(
                f"row {i}: '{column}' = {value!r} already appeared on row {seen[value]}"
            )
        else:
            seen[value] = i
    return problems
