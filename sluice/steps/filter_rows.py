"""Keep only the rows where a column equals, or does not equal, a value."""

from __future__ import annotations

from sluice.context import Row, RunContext
from sluice.errors import StepError

NAME = "filter_rows"
DESCRIPTION = "Keep rows where a column matches (or does not match) a value."


def run(rows: list[Row], options: dict, ctx: RunContext) -> list[Row]:
    column = options.get("column")
    if not column:
        raise StepError("no 'column' given", step=NAME)
    if "equals" not in options and "not_equals" not in options:
        raise StepError(
            "need either 'equals' or 'not_equals'",
            step=NAME,
            hint='e.g.  column = "status"\n        equals = "active"',
        )

    if rows and column not in rows[0]:
        raise StepError(
            f"no column '{column}'", step=NAME, hint=f"the rows have: {', '.join(sorted(rows[0]))}"
        )

    if "equals" in options:
        wanted = options["equals"]
        kept = [r for r in rows if r.get(column) == wanted]
    else:
        unwanted = options["not_equals"]
        kept = [r for r in rows if r.get(column) != unwanted]

    dropped = len(rows) - len(kept)
    if dropped:
        ctx.debug(f"dropped {dropped} row(s)")
        ctx.count("rows_filtered_out", dropped)
    return kept
