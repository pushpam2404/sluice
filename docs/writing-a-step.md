# Writing a step

A step takes rows and returns rows. That is the whole contract.

Adding one means adding **one file**. Nothing central has to be edited, so you
will never conflict with somebody else adding a different step.

---

## The shape

Create `sluice/steps/your_step.py`:

```python
"""One line saying what this does."""

from __future__ import annotations

from sluice.context import Row, RunContext
from sluice.errors import StepError

NAME = "your_step"
DESCRIPTION = "One sentence, ending in a full stop."


def run(rows: list[Row], options: dict, ctx: RunContext) -> list[Row]:
    return rows
```

That is enough to be discovered. `python -m sluice stages` will list it
immediately — there is no registration step.

| Thing | Rule |
|---|---|
| `NAME` | What a pipeline file writes after `use =`. Lower case with underscores. Must be unique across steps *and* checks. |
| `DESCRIPTION` | One sentence, ending in a full stop. It appears in `sluice stages`, and a test enforces the full stop. |
| `run()` | Takes `(rows, options, ctx)` and returns a **new** list of rows. |

---

## The four rules

**1. Return a new list. Do not modify the one you were given.**

```python
# yes
return [{**row, "country": row["country"].upper()} for row in rows]

# no — this edits the caller's data underneath them
for row in rows:
    row["country"] = row["country"].upper()
return rows
```

There is a test for this on `rename_columns`. Add the equivalent for yours.

**2. Validate options first, before touching any data.**

Discovering on row 400,000 that `path` was missing has wasted four minutes and
told the user nothing useful. Check at the top.

```python
path = options.get("path")
if not path:
    raise StepError("no 'path' given", step=NAME,
                    hint='add  path = "data/customers.csv"')
```

**3. Every error says where and suggests a fix.**

This is the whole point of the project. Compare:

```
KeyError: 'customer_id'
```

against:

```
step 'rename_columns': cannot rename column(s) that are not there: customer_id
  hint: the rows have: cust_id, full_name, email, status
```

The second one ends the problem. `StepError` takes `step=`, an optional `row=`,
and an optional `hint=` — use all three when you can.

**4. Count what you did.**

```python
ctx.count("rows_filtered_out", dropped)
ctx.debug(f"dropped {dropped} row(s)")
```

`ctx.debug` only prints under `-v`. `ctx.log` always prints. A run that says
only "finished" is not auditable a week later.

---

## Testing it

Add `tests/test_steps.py::TestYourStep`. Cover, at minimum:

- the happy path
- every option that can be missing or wrong
- that the input rows were not modified
- what happens on an empty list

Look at `TestWriteSqlite` for the shape. Note that it asserts on the *message*,
not just that something was raised — an error nobody can act on is a bug even
if it is technically correct.

```bash
python -m pytest tests/test_steps.py -v
```

---

## Trying it for real

Add it to a pipeline file and run it:

```toml
[[stage]]
use = "your_step"
some_option = "value"
```

```bash
python -m sluice run pipelines/yours.toml -v
python -m sluice explain your_step
```

---

## Before you open the pull request

- [ ] `python -m sluice stages` lists it
- [ ] `python -m sluice explain your_step` reads sensibly
- [ ] `python -m pytest` passes
- [ ] `ruff check .` is clean
- [ ] Every error you raise names the step and suggests a fix
- [ ] You did not modify the rows you were given

---

## If your idea does not fit this shape

Then it may be a **check** rather than a step — see
[writing-a-check.md](writing-a-check.md) — or it may be a change to the runner
itself, which is a bigger conversation. Open an issue and describe it before
writing much; that is a genuinely useful contribution in its own right.
