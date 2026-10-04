"""Shared fixtures.

Nothing here touches the network or a real database. Every test runs against a
temporary directory, so the suite is safe to run anywhere and leaves nothing
behind.
"""

from __future__ import annotations

import pytest

from sluice.context import RunContext


@pytest.fixture
def ctx() -> RunContext:
    """A quiet run context — tests should not print unless they mean to."""
    import io

    return RunContext(pipeline="test", _stream=io.StringIO())


@pytest.fixture
def rows() -> list[dict]:
    return [
        {"customer_id": "1", "name": "Asha", "status": "active"},
        {"customer_id": "2", "name": "Ben", "status": "churned"},
        {"customer_id": "3", "name": "Chen", "status": "active"},
    ]


@pytest.fixture
def csv_file(tmp_path):
    path = tmp_path / "people.csv"
    path.write_text(
        "cust_id,full_name,status\n1,Asha,active\n2,Ben,churned\n3,Chen,active\n",
        encoding="utf-8",
    )
    return path
