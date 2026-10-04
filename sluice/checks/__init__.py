"""Checks inspect rows and report problems. They never change the data.

One file per check. Each declares NAME, DESCRIPTION and a check() function:

    def check(rows: list[dict], options: dict, ctx: RunContext) -> list[str]

Returning an empty list means the data is fine. Returning strings means it is
not, and each string should name the row and what was wrong with it.

See docs/writing-a-check.md.
"""
