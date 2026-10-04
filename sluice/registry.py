"""Finding the steps and checks that exist.

Both are discovered by importing every module in `sluice/steps/` and
`sluice/checks/` and looking at what they declare. Nothing has to be listed in
a central file, which is deliberate: it means adding one is adding one file,
and two people adding two different steps never touch the same line.

A step transforms rows and returns new ones.
A check inspects rows and returns problems. A check must never change the data
— that separation is the point, and it is enforced here rather than left to
good intentions.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable
from dataclasses import dataclass
from types import ModuleType
from typing import Any

from sluice.context import Row, RunContext
from sluice.errors import ConfigError


@dataclass(frozen=True)
class Stage:
    """One thing a pipeline can do. Either a step or a check, never both."""

    name: str
    kind: str  # "step" or "check"
    description: str
    run: Callable[..., Any]
    module: str


_REGISTRY: dict[str, Stage] | None = None


def _load_package(package_name: str, kind: str) -> dict[str, Stage]:
    package = importlib.import_module(package_name)
    found: dict[str, Stage] = {}

    for info in pkgutil.iter_modules(package.__path__):
        if info.name.startswith("_"):
            continue
        module: ModuleType = importlib.import_module(f"{package_name}.{info.name}")

        name = getattr(module, "NAME", None)
        description = getattr(module, "DESCRIPTION", "")
        entry = getattr(module, "run", None) if kind == "step" else getattr(module, "check", None)

        if name is None or entry is None:
            # A half-written module is a mistake, not a feature. Say so loudly
            # rather than silently leaving the stage out of the registry.
            raise ConfigError(
                f"{package_name}.{info.name} does not look like a {kind}",
                hint=(
                    f"a {kind} module must define NAME, DESCRIPTION and a "
                    f"{'run' if kind == 'step' else 'check'}() function. "
                    f"See docs/writing-a-{kind}.md"
                ),
            )

        if name in found:
            raise ConfigError(
                f"two {kind}s both call themselves '{name}'",
                hint="NAME must be unique across the package",
            )

        found[name] = Stage(
            name=name,
            kind=kind,
            description=description,
            run=entry,
            module=f"{package_name}.{info.name}",
        )

    return found


def registry(*, refresh: bool = False) -> dict[str, Stage]:
    """Every stage available, keyed by the name a pipeline file would use."""
    global _REGISTRY
    if _REGISTRY is None or refresh:
        combined = _load_package("sluice.steps", "step")
        checks = _load_package("sluice.checks", "check")

        overlap = set(combined) & set(checks)
        if overlap:
            raise ConfigError(
                f"a step and a check share the name(s): {', '.join(sorted(overlap))}",
                hint="names must be unique across both packages",
            )

        combined.update(checks)
        _REGISTRY = combined
    return _REGISTRY


def lookup(name: str) -> Stage:
    """Find one stage by name, or explain what the options were."""
    table = registry()
    if name not in table:
        close = [k for k in table if k.startswith(name[:3])]
        hint = f"did you mean: {', '.join(sorted(close))}?" if close else None
        raise ConfigError(
            f"no step or check called '{name}'",
            hint=hint or f"available: {', '.join(sorted(table))}",
        )
    return table[name]


def describe_all() -> list[Stage]:
    return sorted(registry().values(), key=lambda s: (s.kind, s.name))


__all__ = ["Stage", "registry", "lookup", "describe_all", "Row", "RunContext"]
