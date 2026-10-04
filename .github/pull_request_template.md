<!--
  Thanks for contributing to sluice.
  Pull requests that leave this blank are closed without review.
-->

## Which issue?

Closes #

<!-- Required. Without it the issue has to be closed by hand, which is how issues get forgotten. -->

## What changed, and why that way?

<!--
  The diff shows what you did. This is for what you considered and rejected.

  On an `advanced` issue this is the main thing being reviewed. One short
  paragraph is plenty:

    "I went with X rather than Y because Y means the row count is no longer
     knowable without consuming the iterator, and that log line is one of the
     more useful things the tool prints."
-->

## Tests

<!-- Which tests did you add, and what do they fail on without your change? -->

```
$ python -m pytest

```

## Checklist

- [ ] I commented `/claim` on the issue and it is assigned to me
- [ ] `python -m pytest` passes
- [ ] `ruff check . --select F,B` is clean
- [ ] I added a test that fails without this change
- [ ] Every error I raise names where it happened and suggests a fix
- [ ] Steps return a new list; checks do not modify rows
- [ ] No new runtime dependency
- [ ] If this changes a design decision, I updated `docs/design-decisions.md`
- [ ] If I used an AI tool, I can explain the reasoning in review

---

<sub>First time here? Read [CONTRIBUTING.md](../blob/main/CONTRIBUTING.md) and [docs/design-decisions.md](../blob/main/docs/design-decisions.md).</sub>
