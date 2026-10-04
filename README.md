<h1 align="center">sluice</h1>

<p align="center">A small data pipeline runner that refuses to fail quietly.<br>
Built for people who already write code and want somewhere real to practise.</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/dependencies-none-1F883D" alt="No dependencies">
  <img src="https://img.shields.io/badge/level-intermediate%20%2F%20advanced-D93F0B" alt="Intermediate / advanced">
  <img src="https://img.shields.io/badge/license-MIT-lightgrey" alt="MIT">
</p>

---

## The idea

Most data pipelines fail the same way: they don't. They run, they report
success, and six weeks later somebody notices the revenue number has been wrong
since March because a column quietly started arriving empty.

`sluice` is a tiny pipeline runner built around the opposite instinct. Checks
sit between steps, failures stop the run, and every error says which row, which
column, and what to do about it.

```
CheckFailed: check 'unique' failed: 1 problem(s) in 4,812 rows
    - row 3,109: 'customer_id' = '70412' already appeared on row 882
```

Not `KeyError: 'customer_id'`.

---

## Run it

Python 3.11 or newer. Nothing else — no dependencies, no install step.

```bash
git clone https://github.com/pushpam2404/sluice.git
cd sluice
python -m sluice run pipelines/customers.toml -v
```

```
[  0.00s] info  pipeline 'customers' starting (run 5b0e395c1409)
[  0.00s] info  1/7 read_csv: 0 -> 6 rows
[  0.00s] info  2/7 row_count: passed on 6 rows
[  0.00s] info  3/7 rename_columns: 6 -> 6 rows
[  0.00s] info  4/7 not_null: passed on 6 rows
[  0.00s] info  5/7 unique: passed on 6 rows
[  0.00s] info  6/7 filter_rows: 6 -> 4 rows
[  0.00s] info  wrote 4 rows to warehouse.db:customers
[  0.01s] info  pipeline 'customers' finished: 4 rows in 0.01s
```

Every stage says what went in and what came out. A row that disappears is a row
you can account for.

---

## A pipeline

One TOML file. Stages run top to bottom.

```toml
name = "customers"

[[stage]]
use  = "read_csv"
path = "pipelines/data/customers.csv"

[[stage]]
use = "row_count"
min = 1                      # refuse to carry on with an empty extract

[[stage]]
use     = "rename_columns"
mapping = { cust_id = "customer_id" }

[[stage]]
use     = "not_null"
columns = ["customer_id", "email"]

[[stage]]
use      = "write_sqlite"
database = "warehouse.db"
table    = "customers"
```

A **step** transforms rows. A **check** inspects them and never changes them.
Putting a check between two steps catches a problem where it appears, instead
of three stages later.

```bash
python -m sluice stages            # everything available
python -m sluice explain read_csv  # what one does
python -m sluice run x.toml --dry-run
```

---

## Where to look, and what to ignore

### 🎯 Your work almost certainly goes here

| Folder | What is in it |
|---|---|
| **`sluice/steps/`** | **One file per step.** Adding one means adding one file — nothing central to edit, so two people never conflict. |
| **`sluice/checks/`** | **One file per check.** Same pattern. |
| `tests/` | One test module per area. Every issue expects tests. |

### 📖 Read before changing

| File | Why |
|---|---|
| **`docs/design-decisions.md`** | **Start here.** Every decision that could reasonably have gone the other way, and what would change it. Several open issues are arguments with this file. |
| `docs/writing-a-step.md` | The contract, the four rules, the checklist |
| `docs/writing-a-check.md` | Same, for checks |
| `sluice/errors.py` | The error taxonomy. The whole project hangs off it |

### 🙈 The runner itself

`pipeline.py`, `registry.py`, `context.py`, `cli.py`. Changing these is welcome
but is a bigger conversation — open an issue first.

---

## Contributing

This is not a beginner repository. It assumes you can read Python, write a
test, and argue for a design choice. If you want somewhere gentler to start,
[open-source-launchpad](https://github.com/pushpam2404/open-source-launchpad)
and [terminal-arcade](https://github.com/pushpam2404/terminal-arcade) are built
for exactly that.

Issues come in two kinds:

| Label | What it means |
|---|---|
| `difficulty: intermediate` | A clear job. You will touch two or three files and write tests. |
| `difficulty: advanced` | **A judgement call.** Two or more defensible answers exist, and the pull request has to argue for one. |

The advanced ones are the interesting ones. An issue titled *"rows are all held
in memory"* is not asking you to add streaming — it is asking whether streaming
is worth what it costs, and the answer might be no.

**On those, comment before you build.** A good argument on the issue is worth
more than a large pull request nobody asked for.

Full guide in [CONTRIBUTING.md](CONTRIBUTING.md).

---

## What this is not

Not Airflow. No scheduler, no DAG, no backfills, no UI, no distributed
anything. It runs one pipeline, now, on your laptop.

That is deliberate. It is small enough to read in an afternoon, which is what
makes it a good place to learn what the big ones are actually doing.

---

## License

MIT — see [LICENSE](LICENSE).
