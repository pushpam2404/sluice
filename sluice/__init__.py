"""sluice — a small, local-first data pipeline runner that refuses to fail quietly."""

__version__ = "0.1.0"

from sluice.errors import (
    CheckFailed,
    ConfigError,
    SchemaDrift,
    SluiceError,
    StepError,
)

__all__ = [
    "__version__",
    "SluiceError",
    "ConfigError",
    "StepError",
    "CheckFailed",
    "SchemaDrift",
]
