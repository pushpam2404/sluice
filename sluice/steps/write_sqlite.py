"""Write rows into a SQLite table.

Loading is where a pipeline stops being reversible, so this is the step that
most needs to be deliberate about what "running it twice" means. Right now it
replaces the table every time. That is the safe default but not the only sane
one — see docs/design-decisions.md.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from sluice.context import Row, RunContext
from sluice.errors import StepError

NAME = "write_sqlite"
DESCRIPTION = "Write rows into a SQLite table, replacing whatever was there."


def run(rows: list[Row], options: dict, ctx: RunContext) -> list[Row]:
    database = options.get("database")
    table = options.get("table")

    if not database:
        raise StepError("no 'database' given", step=NAME, hint='database = "warehouse.db"')
    if not table:
        raise StepError("no 'table' given", step=NAME, hint='table = "customers"')
    if not table.replace("_", "").isalnum():
        raise StepError(
            f"'{table}' is not a safe table name",
            step=NAME,
            hint="letters, digits and underscores only — the name goes into SQL directly",
        )

    if not rows:
        ctx.warn(f"nothing to write to {table} — the pipeline produced 0 rows")
        return rows

    if ctx.dry_run:
        ctx.log(f"dry run: would write {len(rows)} rows to {database}:{table}")
        return rows

    columns = list(rows[0])
    for i, row in enumerate(rows, start=1):
        if list(row) != columns:
            raise StepError(
                "rows do not all have the same columns",
                step=NAME,
                row=i,
                hint=f"row 1 has {columns}, row {i} has {list(row)}",
            )

    Path(database).parent.mkdir(parents=True, exist_ok=True)

    column_sql = ", ".join(f'"{c}" TEXT' for c in columns)
    quoted = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join("?" for _ in columns)

    with sqlite3.connect(database) as conn:
        conn.execute(f'DROP TABLE IF EXISTS "{table}"')
        conn.execute(f'CREATE TABLE "{table}" ({column_sql})')
        conn.executemany(
            f'INSERT INTO "{table}" ({quoted}) VALUES ({placeholders})',
            [tuple(str(row[c]) for c in columns) for row in rows],
        )

    ctx.log(f"wrote {len(rows)} rows to {database}:{table}")
    ctx.count("rows_written", len(rows))
    return rows
