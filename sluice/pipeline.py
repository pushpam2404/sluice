"""Reading a pipeline file and running it.

A pipeline is a TOML file listing stages in order. Each stage names a step or a
check; everything else in the table is passed to it as options.

    name = "customers"

    [[stage]]
    use  = "read_csv"
    path = "pipelines/data/customers.csv"

    [[stage]]
    use     = "not_null"
    columns = ["customer_id"]

Order is explicit and literal. There is no dependency graph and no clever
scheduling — stages run top to bottom. That is a deliberate limitation, written
down in docs/design-decisions.md, and arguing with it is a legitimate
contribution.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sluice.context import Row, RunContext
from sluice.errors import CheckFailed, ConfigError, SluiceError, StepError
from sluice.registry import lookup


@dataclass
class StageSpec:
    use: str
    options: dict[str, Any]
    index: int


@dataclass
class Pipeline:
    name: str
    stages: list[StageSpec]
    source: Path | None = None


def load(path: str | Path) -> Pipeline:
    """Parse a pipeline file, failing on anything suspicious before data is touched."""
    path = Path(path)
    if not path.exists():
        raise ConfigError(
            f"no pipeline file at {path}",
            hint="pipelines/ holds the examples that ship with the project",
        )

    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path} is not valid TOML: {exc}") from exc

    name = raw.get("name")
    if not name or not isinstance(name, str):
        raise ConfigError(
            f"{path} has no 'name'",
            hint='add a line at the top:  name = "customers"',
        )

    stages_raw = raw.get("stage")
    if not stages_raw:
        raise ConfigError(
            f"{path} defines no stages",
            hint="add at least one [[stage]] table with a 'use' key",
        )
    if not isinstance(stages_raw, list):
        raise ConfigError(
            f"{path}: 'stage' must be a list of tables",
            hint="use [[stage]] with two brackets, not [stage]",
        )

    stages: list[StageSpec] = []
    for i, entry in enumerate(stages_raw, start=1):
        if not isinstance(entry, dict):
            raise ConfigError(f"{path}: stage {i} is not a table")
        use = entry.get("use")
        if not use:
            raise ConfigError(
                f"{path}: stage {i} has no 'use'",
                hint='every stage needs one, e.g.  use = "read_csv"',
            )
        lookup(use)  # fail now, not halfway through a run
        options = {k: v for k, v in entry.items() if k != "use"}
        stages.append(StageSpec(use=use, options=options, index=i))

    return Pipeline(name=name, stages=stages, source=path)


def run(pipeline: Pipeline, ctx: RunContext | None = None) -> list[Row]:
    """Execute every stage in order and return whatever came out of the last one."""
    ctx = ctx or RunContext(pipeline=pipeline.name)
    rows: list[Row] = []

    ctx.log(f"pipeline '{pipeline.name}' starting (run {ctx.run_id})")
    if ctx.dry_run:
        ctx.log("dry run — nothing will be written")

    for spec in pipeline.stages:
        stage = lookup(spec.use)
        label = f"{spec.index}/{len(pipeline.stages)} {stage.name}"

        try:
            if stage.kind == "step":
                before = len(rows)
                rows = stage.run(rows, spec.options, ctx)
                if not isinstance(rows, list):
                    raise StepError(
                        f"returned {type(rows).__name__}, not a list of rows",
                        step=stage.name,
                        hint="a step must return a list of dicts. See docs/writing-a-step.md",
                    )
                ctx.log(f"{label}: {before} -> {len(rows)} rows")
                ctx.count(f"rows_out.{stage.name}", len(rows))
            else:
                problems = stage.run(rows, spec.options, ctx)
                if problems:
                    raise CheckFailed(
                        f"{len(problems)} problem(s) in {len(rows)} rows",
                        check=stage.name,
                        failures=[str(p) for p in problems],
                    )
                ctx.log(f"{label}: passed on {len(rows)} rows")
                ctx.count(f"checks_passed.{stage.name}")

        except SluiceError:
            raise
        except Exception as exc:
            # Anything a stage did not anticipate still gets named and located,
            # rather than surfacing as a bare traceback with no context.
            raise StepError(
                f"unexpected {type(exc).__name__}: {exc}",
                step=stage.name,
                hint="if this is a bug in the stage itself, that is worth an issue",
            ) from exc

    ctx.log(f"pipeline '{pipeline.name}' finished: {len(rows)} rows in {ctx.elapsed():.2f}s")
    return rows


__all__ = ["Pipeline", "StageSpec", "load", "run"]
