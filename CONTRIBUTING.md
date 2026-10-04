# Contributing

Thanks for being here.

This is not a beginner repository. It assumes you can read Python, write a test,
and make a case for a design choice. If you want somewhere gentler to start,
[open-source-launchpad](https://github.com/pushpam2404/open-source-launchpad)
and [terminal-arcade](https://github.com/pushpam2404/terminal-arcade) exist for
exactly that, and starting there is not a lesser thing to do.

---

## Setup

Python 3.11 or newer. That is the whole list.

```bash
git clone https://github.com/YOUR-USERNAME/sluice.git
cd sluice
python -m sluice run pipelines/customers.toml -v
python -m pytest
```

No dependencies to install. For the dev tools:

```bash
pip install -e ".[dev]"     # pytest and ruff
```

---

## The two kinds of issue

| Label | What it is |
|---|---|
| `difficulty: intermediate` | A clear job with a known shape. Two or three files, plus tests. |
| `difficulty: advanced` | **A judgement call.** Two or more defensible answers exist. |

**The advanced ones are not just bigger.** They are open questions. An issue
titled *"rows are all held in memory"* is not asking you to add streaming — it
is asking whether streaming is worth what it costs, and *no* is a valid answer
if you argue it well.

Before building one of those:

1. Read the relevant section of [docs/design-decisions.md](docs/design-decisions.md)
2. **Comment on the issue with your approach** and why you prefer it
3. Wait for a reply — usually within 48 hours

This is not bureaucracy. A 400-line pull request taking an approach the project
has already rejected wastes your evening, and that is a worse outcome than a
short conversation first.

---

## Claiming

Comment `/claim`. A bot assigns it to you.

Two at a time. Go quiet for five days and the bot releases it — no hard
feelings, come back and claim another.

---

## The workflow

```bash
git checkout -b feat/streaming-rows
# ... work ...
python -m pytest
ruff check . --fix
ruff format .
git commit -m "feat: stream rows between stages"
git push -u origin feat/streaming-rows
```

Branch prefixes: `feat/`, `fix/`, `docs/`, `test/`, `refactor/`, `ci/`.
Commit messages as `type: what changed`.

Your pull request description must contain `Closes #12`.

---

## What a good pull request looks like here

**Tests are not optional.** Every behaviour change needs a test that fails
without your change. The existing suite is the model: look at how
`tests/test_steps.py` asserts on the error *message*, not just that something
was raised.

**Explain the choice, not the diff.** The diff is visible. What is not visible
is what else you considered. One short paragraph:

> I went with X rather than Y because Y would mean the row count is no longer
> knowable without consuming the iterator, and that log line is one of the more
> useful things the tool prints.

**Keep it to one issue.** A pull request fixing three things is three times
harder to review and will sit three times longer.

**If you changed a design decision, update the document.**
`docs/design-decisions.md` is meant to be current. Changing the answer without
changing the page leaves the next person misled.

---

## The rules that are not negotiable

A few things are load-bearing. Changing them is not a contribution, it is a
different project:

- **A check never modifies rows.** Validation and repair are different jobs.
  A check that quietly fixes things makes both the data and the report
  untrustworthy.
- **A step returns a new list.** It does not edit its input in place.
- **Every error says where and suggests a fix.** `KeyError: 'customer_id'` is
  not acceptable output from this tool.
- **No runtime dependencies.** `git clone` and run. Dev tools are fine.

Each of these is explained in [docs/design-decisions.md](docs/design-decisions.md).
If you think one is wrong, the issue tracker is the place — and a persuasive
argument would be genuinely welcome.

---

## What gets declined

| | Why |
|---|---|
| No tests | Every behaviour change needs one |
| Several unrelated changes at once | Unreviewable |
| A design decision reversed with no argument | The decision was deliberate; read the doc and make a case |
| A check that modifies rows | Load-bearing rule |
| A new runtime dependency | See design decision 8 |
| Reformatting files you did not otherwise change | Buries the real change in noise |

If yours is closed for one of these it is not personal. Ask on the issue and we
will work out what would land.

---

## Automatic checks

| Blocks the merge | Does not block |
|---|---|
| A failing test | Spacing, quote marks, import order |
| A real bug — undefined name, unused import, mutable default argument | A missing trailing newline |
| A shipped pipeline that no longer runs | Line length |
| A step or check missing `NAME`/`DESCRIPTION` | |

Reproduce any of them locally:

```bash
python -m pytest
ruff check . --select F,B
python -m sluice run pipelines/customers.toml
```

Formatting never blocks you. That is deliberate.

---

## Using AI

Fine. Expected, even.

What is not fine is a pull request you cannot explain. On an advanced issue you
will be asked *why* you chose this approach, and "it is what the model
suggested" is not an answer. The reasoning is the contribution here; the code is
the easy part.

---

## Maintainers

| Name | GitHub | Looks after |
|---|---|---|
| Pushpam Raj Satyarthi | [@pushpam2404](https://github.com/pushpam2404) | Everything |

By taking part you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
