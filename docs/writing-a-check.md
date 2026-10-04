# Writing a check

A check looks at rows and reports what is wrong with them. **It never changes
them.** That separation is the most important rule in the project — see
[design-decisions.md](design-decisions.md#6-checks-cannot-modify-rows).

Adding one means adding **one file**, same as a step.

---

## The shape

Create `sluice/checks/your_check.py`:

```python
"""One line saying what this catches."""

from __future__ import annotations

from sluice.context import Row, RunContext
from sluice.errors import ConfigError

NAME = "your_check"
DESCRIPTION = "One sentence, ending in a full stop."


def check(rows: list[Row], options: dict, ctx: RunContext) -> list[str]:
    problems: list[str] = []
    for i, row in enumerate(rows, start=1):
        if something_is_wrong(row):
            problems.append(f"row {i}: what exactly was wrong")
    return problems
```

Return an **empty list** when the data is fine. Return strings when it is not.
The runner turns a non-empty list into a `CheckFailed` and stops the pipeline.

Note the function is called `check`, not `run`. That is how the registry tells
the two kinds apart.

---

## What makes a good problem message

A check's output is read by somebody who has to go and fix the data, possibly
in a file with four million lines. Give them the row number and the value.

```python
# useless
problems.append("invalid email")

# useful
problems.append(f"row {i}: 'email' = {value!r} has no @")
```

Rows are numbered from 1, matching how a spreadsheet shows them.

---

## Options

Validate them at the top and raise `ConfigError`, not `CheckFailed` — a missing
option is the pipeline author's mistake, not the data's.

```python
column = options.get("column")
if not column:
    raise ConfigError(f"{NAME} needs 'column'", hint='column = "customer_id"')
```

---

## Report everything, not just the first thing

Somebody fixing data wants the whole list, not to rerun the pipeline once per
bad row. Collect every problem and return them all. The error formatter shows
the first ten and counts the rest, so a wholly broken file does not fill the
terminal.

---

## Testing it

Add `tests/test_checks.py::TestYourCheck`. Cover:

- clean data returns `[]`
- each kind of problem is caught
- the message names the row and the column
- the rows were not modified
- a missing option raises `ConfigError`

That last-but-one matters. Every check has a test like this:

```python
def test_does_not_change_the_data(self, ctx):
    rows = [{"a": ""}]
    your_check.check(rows, {"columns": ["a"]}, ctx)
    assert rows == [{"a": ""}], "a check must never modify rows"
```

---

## Before you open the pull request

- [ ] `python -m sluice stages` lists it under CHECKS
- [ ] `python -m pytest` passes
- [ ] `ruff check .` is clean
- [ ] Every message names the row and the value
- [ ] It returns `[]` on clean data rather than raising
- [ ] It does not modify the rows
