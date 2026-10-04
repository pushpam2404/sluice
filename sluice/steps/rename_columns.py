"""Rename columns."""

from __future__ import annotations

from sluice.context import Row, RunContext
from sluice.errors import StepError

NAME = "rename_columns"
DESCRIPTION = "Rename columns, e.g. cust_id -> customer_id."


def run(rows: list[Row], options: dict, ctx: RunContext) -> list[Row]:
    mapping = options.get("mapping")
    if not mapping:
        raise StepError(
            "no 'mapping' given", step=NAME, hint='mapping = { cust_id = "customer_id" }'
        )
    if not isinstance(mapping, dict):
        raise StepError("'mapping' must be a table of old = \"new\"", step=NAME)

    if rows:
        present = set(rows[0])
        missing = set(mapping) - present
        if missing:
            raise StepError(
                f"cannot rename column(s) that are not there: {', '.join(sorted(missing))}",
                step=NAME,
                hint=f"the rows have: {', '.join(sorted(present))}",
            )

    return [{mapping.get(k, k): v for k, v in row.items()} for row in rows]
