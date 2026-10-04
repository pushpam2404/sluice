"""The command line.

    python -m sluice run pipelines/customers.toml
    python -m sluice stages
    python -m sluice explain read_csv

Errors print as a sentence a person can act on, not a traceback. A traceback is
for a bug in sluice itself; a bad pipeline file is not a bug and should not look
like one. --traceback brings the full one back when you are debugging sluice.
"""

from __future__ import annotations

import argparse
import sys

from sluice import __version__
from sluice.context import RunContext
from sluice.errors import SluiceError
from sluice.registry import describe_all, lookup


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sluice",
        description="Run a small data pipeline that refuses to fail quietly.",
    )
    parser.add_argument("--version", action="version", version=f"sluice {__version__}")
    sub = parser.add_subparsers(dest="command")

    run_cmd = sub.add_parser("run", help="run a pipeline file")
    run_cmd.add_argument("pipeline", help="path to a .toml pipeline")
    run_cmd.add_argument("-v", "--verbose", action="store_true", help="show per-stage detail")
    run_cmd.add_argument(
        "--dry-run", action="store_true", help="run everything except the steps that write"
    )
    run_cmd.add_argument(
        "--traceback", action="store_true", help="show the full Python traceback on failure"
    )

    sub.add_parser("stages", help="list every step and check available")

    explain = sub.add_parser("explain", help="describe one step or check")
    explain.add_argument("name")

    return parser


def cmd_stages() -> int:
    steps = [s for s in describe_all() if s.kind == "step"]
    checks = [s for s in describe_all() if s.kind == "check"]

    print("STEPS — these transform rows\n")
    for s in steps:
        print(f"  {s.name:<18} {s.description}")
    print("\nCHECKS — these inspect rows and never change them\n")
    for c in checks:
        print(f"  {c.name:<18} {c.description}")
    print(f"\n{len(steps)} steps, {len(checks)} checks.")
    print("Add one by adding one file — see docs/writing-a-step.md")
    return 0


def cmd_explain(name: str) -> int:
    stage = lookup(name)
    print(f"{stage.name}  ({stage.kind})")
    print(f"  {stage.description}")
    print(f"  defined in {stage.module.replace('.', '/')}.py")
    doc = (stage.run.__doc__ or "").strip()
    if doc:
        print()
        for line in doc.splitlines():
            print(f"  {line}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from sluice import pipeline as pipeline_module

    spec = pipeline_module.load(args.pipeline)
    ctx = RunContext(pipeline=spec.name, verbose=args.verbose, dry_run=args.dry_run)
    pipeline_module.run(spec, ctx)

    if args.verbose and ctx.counters:
        print("\ncounters:", file=sys.stderr)
        for key in sorted(ctx.counters):
            print(f"  {key:<32} {ctx.counters[key]:>8,}", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "stages":
            return cmd_stages()
        if args.command == "explain":
            return cmd_explain(args.name)
        if args.command == "run":
            return cmd_run(args)
    except SluiceError as exc:
        if getattr(args, "traceback", False):
            raise
        print(f"\n{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
