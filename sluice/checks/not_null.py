"""Fail if named columns are empty anywhere."""

from __future__ import annotations

from sluice.context import Row, RunContext
from sluice.errors import ConfigError

NAME = "not_null"
DESCRIPTION = "Fail if any of the named columns is empty in any row."


def check(rows: list[Row], options: dict, ctx: RunContext) -> list[str]:
    columns = options.get("columns")
    if not columns:
        raise ConfigError(f"{NAME} needs 'columns'", hint='columns = ["customer_id", "email"]')
    if isinstance(columns, str):
        columns = [columns]

    problems: list[str] = []
    for i, row in enumerate(rows, start=1):
        for column in columns:
            if column not in row:
                problems.append(f"row {i}: no column '{column}'")
            elif row[column] is None or str(row[column]).strip() == "":
                problems.append(f"row {i}: '{column}' is empty")
    return problems
