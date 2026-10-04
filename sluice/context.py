"""What a single pipeline run knows about itself.

Passed to every step and every check. Carries the run id, a logger that writes
in one consistent shape, and the counters that make a run auditable after the
fact — "it succeeded" is not a useful thing to know a week later, "it read
4,812 rows and wrote 4,790, dropping 22 at the not_null check" is.
"""

from __future__ import annotations

import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

Row = dict[str, Any]


@dataclass
class RunContext:
    pipeline: str
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    started_at: float = field(default_factory=time.time)
    verbose: bool = False
    dry_run: bool = False
    counters: dict[str, int] = field(default_factory=dict)
    _stream: Any = field(default=None, repr=False)

    @property
    def stream(self) -> Any:
        return self._stream if self._stream is not None else sys.stderr

    def count(self, name: str, by: int = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + by

    def log(self, message: str, *, level: str = "info") -> None:
        if level == "debug" and not self.verbose:
            return
        elapsed = time.time() - self.started_at
        print(f"[{elapsed:6.2f}s] {level:<5} {message}", file=self.stream)

    def debug(self, message: str) -> None:
        self.log(message, level="debug")

    def warn(self, message: str) -> None:
        self.log(message, level="warn")

    def error(self, message: str) -> None:
        self.log(message, level="error")

    def elapsed(self) -> float:
        return time.time() - self.started_at
