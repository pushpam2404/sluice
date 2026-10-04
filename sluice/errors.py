"""The error taxonomy.

The whole point of this project is that a pipeline should fail loudly rather
than quietly producing wrong numbers. That only works if failures are
distinguishable: "the config is wrong" and "the data is wrong" need different
reactions, and a human reading a log at 3am needs to tell them apart instantly.

Every error carries enough context to act on. An exception that says only
"KeyError: 'customer_id'" has told you nothing you can use.
"""

from __future__ import annotations


class SluiceError(Exception):
    """Base class. Catching this catches every error the pipeline raises on purpose."""

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint

    def __str__(self) -> str:
        if self.hint:
            return f"{self.message}\n  hint: {self.hint}"
        return self.message


class ConfigError(SluiceError):
    """The pipeline file is wrong — before any data was read.

    Raised for a missing key, an unknown stage name, a bad type. These are
    always the author's fault and are always fixable by editing the TOML.
    """


class StepError(SluiceError):
    """A step failed while running.

    Carries which step and which row, because "it crashed" is not actionable
    and "row 4,812 of read_csv has a date in a column typed as an integer" is.
    """

    def __init__(
        self,
        message: str,
        *,
        step: str,
        row: int | None = None,
        hint: str | None = None,
    ) -> None:
        super().__init__(message, hint=hint)
        self.step = step
        self.row = row

    def __str__(self) -> str:
        where = f"step '{self.step}'"
        if self.row is not None:
            where += f", row {self.row}"
        out = f"{where}: {self.message}"
        if self.hint:
            out += f"\n  hint: {self.hint}"
        return out


class CheckFailed(SluiceError):
    """A data quality check found something.

    Distinct from StepError on purpose: the pipeline worked, the data did not
    meet expectations. Those call for different responses, and conflating them
    is how bad data gets waved through because "the job succeeded".
    """

    def __init__(
        self,
        message: str,
        *,
        check: str,
        failures: list[str] | None = None,
        hint: str | None = None,
    ) -> None:
        super().__init__(message, hint=hint)
        self.check = check
        self.failures = failures or []

    def __str__(self) -> str:
        out = f"check '{self.check}' failed: {self.message}"
        for line in self.failures[:10]:
            out += f"\n    - {line}"
        if len(self.failures) > 10:
            out += f"\n    ... and {len(self.failures) - 10} more"
        if self.hint:
            out += f"\n  hint: {self.hint}"
        return out


class SchemaDrift(SluiceError):
    """The columns are not what the previous run saw.

    Its own class because silent schema drift is the single most common way a
    pipeline keeps "succeeding" while quietly loading nonsense.
    """

    def __init__(
        self,
        message: str,
        *,
        added: set[str] | None = None,
        removed: set[str] | None = None,
        hint: str | None = None,
    ) -> None:
        super().__init__(message, hint=hint)
        self.added = added or set()
        self.removed = removed or set()

    def __str__(self) -> str:
        out = self.message
        if self.added:
            out += f"\n    new columns:     {', '.join(sorted(self.added))}"
        if self.removed:
            out += f"\n    missing columns: {', '.join(sorted(self.removed))}"
        if self.hint:
            out += f"\n  hint: {self.hint}"
        return out
