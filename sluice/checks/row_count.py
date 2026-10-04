"""Fail if the number of rows is outside what you expected.

A pipeline that silently produces zero rows is the classic failure that looks
like a success. This is the cheapest possible guard against it.
"""

from __future__ import annotations

from sluice.context import Row, RunContext
from sluice.errors import ConfigError

NAME = "row_count"
DESCRIPTION = "Fail if the row count falls outside an expected range."


def check(rows: list[Row], options: dict, ctx: RunContext) -> list[str]:
    minimum = options.get("min")
    maximum = options.get("max")
    if minimum is None and maximum is None:
        raise ConfigError(
            f"{NAME} needs 'min', 'max', or both",
            hint="min = 1   # the usual case: refuse to load nothing",
        )

    count = len(rows)
    problems: list[str] = []
    if minimum is not None and count < minimum:
        problems.append(f"expected at least {minimum} rows, got {count}")
    if maximum is not None and count > maximum:
        problems.append(f"expected at most {maximum} rows, got {count}")
    return problems
