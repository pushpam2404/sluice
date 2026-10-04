"""Steps transform rows.

One file per step. Each declares NAME, DESCRIPTION and a run() function:

    def run(rows: list[dict], options: dict, ctx: RunContext) -> list[dict]

Adding a step means adding one file — nothing central needs editing, so two
people adding two steps never touch the same line.

See docs/writing-a-step.md.
"""
