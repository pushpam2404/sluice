# Design decisions

Every decision here was a choice between options that were all defensible. They
are written down so that a contributor can disagree with one on purpose rather
than by accident — and several of the open issues exist precisely because the
current answer is arguable.

**If you want to change one of these, say so on the issue before you build it.**
A well-argued case for a different answer is worth more here than a
well-implemented version of the current one.

Each entry says what was decided, what else was on the table, and what would
have to be true for the answer to change.

---

## 1. Stages run top to bottom, with no dependency graph

**Decided:** a pipeline is an ordered list. Stage 4 runs after stage 3 because
it is written after it.

**Also considered:** a DAG, where each stage names its inputs and the runner
works out the order — which is what Airflow, Dagster and Prefect all do.

**Why this one:** a list is readable by somebody who has never seen the tool.
You can tell what happens by reading downwards. A DAG only earns its complexity
when you have branching or parallelism, and this has neither.

**What would change it:** the moment a real pipeline needs two independent
branches that join later. Expressing that as a list means either duplicating
work or inventing a convention, and at that point the list is lying about the
structure.

---

## 2. Rows are a list of dictionaries, all held in memory

**Decided:** `list[dict[str, Any]]`, materialised completely between stages.

**Also considered:** generators streaming row by row; columnar batches;
`dataclass` rows with a declared schema.

**Why this one:** you can `print(rows[0])` and understand it. Every step is a
plain function from a list to a list, which is trivially testable and trivially
explainable. For the data sizes this tool is honest about handling, it is fine.

**What would change it:** a file that does not fit in memory. Streaming would
fix that, but it changes what a step *is* — a generator cannot be counted
without consuming it, so `read_csv: 0 -> 4,812 rows` would have to go, and that
log line is one of the most useful things the tool prints. **That trade is a
real one and is not obviously worth making.** There is an open issue about it;
it wants an argument, not just a patch.

---

## 3. `write_sqlite` replaces the whole table every run

**Decided:** `DROP TABLE` then `CREATE` then insert.

**Also considered:** append; upsert on a key; append tagged with the run id and
read through a view.

**Why this one:** running the same pipeline twice gives the same result. That
is the single most valuable property a loader can have while you are learning,
because the failure mode of append — silently doubling your data — is invisible
until somebody asks why revenue looks too high.

**What would change it:** incremental loads, where reprocessing everything is
too slow. Then you need a key and a merge strategy, and you have to decide what
happens to rows that vanished from the source. Deleting them is defensible;
so is keeping them. **This is the most interesting open question in the
project.**

---

## 4. A failing check stops the pipeline

**Decided:** `CheckFailed` is raised and nothing downstream runs.

**Also considered:** quarantine the offending rows and carry on with the rest;
warn and continue; a per-check severity.

**Why this one:** the default should be the safe one. Loading 90% of the data
and not noticing is worse than loading none of it and being told why.

**What would change it:** a source that is *always* slightly dirty, where
stopping means never loading anything. Then quarantining is clearly right — but
quarantined rows have to go somewhere, somebody has to look at them, and a
quarantine nobody reads is just deletion with extra steps. **Any proposal here
needs to answer what happens to the quarantined rows**, not only how to
separate them.

---

## 5. Everything is a string

**Decided:** `read_csv` produces strings, and `write_sqlite` declares every
column `TEXT`.

**Also considered:** inferring types from the data; a declared schema in the
pipeline file.

**Why this one:** inference is wrong at the worst possible moment. A column of
IDs that looks numeric until the one that starts with a zero, a date that parses
as American in one file and European in the next. Strings are honest about
having done nothing.

**What would change it:** needing to compute. You cannot sum a string, so the
first aggregation step forces this open. The question is *where* types get
declared — in the pipeline file, which is explicit but verbose, or in a step
that converts, which composes better. **Both are reasonable.**

---

## 6. Checks cannot modify rows

**Decided:** a check returns a list of problem descriptions. Whatever it
returns, the rows carry on unchanged.

**Also considered:** letting a check clean up what it finds.

**Why this one:** "validate" and "repair" are different jobs, and a check that
quietly fixes things is the worst possible tool — you stop being able to trust
either the data or the report. If something should be repaired, that is a step,
and it should be visible in the pipeline file.

**What would change it:** nothing. This one is load-bearing. A contribution
that blurs it will be declined, which is why it is written down here rather
than left implicit.

---

## 7. The registry finds stages by scanning the package

**Decided:** `sluice/steps/` and `sluice/checks/` are imported at startup and
anything declaring `NAME` and `run`/`check` is registered.

**Also considered:** a central list; entry points; an explicit decorator.

**Why this one:** adding a step is adding one file. Nothing central has to be
edited, so two people adding two steps never touch the same line and never
conflict.

**Costs, honestly:** importing everything at startup means a broken module
breaks the whole tool rather than just itself, and the registry caches the
function object, so patching a module after startup has no effect until it is
rebuilt. Both are real. Neither has hurt enough yet to be worth fixing.

---

## 8. No dependencies at all

**Decided:** standard library only. `tomllib` is why the minimum is Python 3.11.

**Also considered:** `pydantic` for validation, `rich` for output, `click` for
the CLI — all of which would make parts of this nicer.

**Why this one:** `git clone` and run. Nothing to install, nothing to go stale,
no lockfile to argue about. For a project people are meant to contribute to on
a borrowed laptop on bad wifi, that is worth more than prettier output.

**What would change it:** something genuinely hard to do well by hand.
Date parsing is the honest candidate. Prettier colours are not.
