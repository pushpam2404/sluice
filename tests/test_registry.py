"""Discovery is what lets a contributor add a step by adding one file.

If these break, adding a step silently stops working, which is the kind of
failure that wastes somebody's afternoon.
"""

from __future__ import annotations

import pytest

from sluice.errors import ConfigError
from sluice.registry import describe_all, lookup, registry


def test_every_shipped_step_and_check_is_discovered():
    table = registry(refresh=True)
    for expected in ("read_csv", "read_json", "rename_columns", "filter_rows", "write_sqlite"):
        assert expected in table, f"{expected} was not discovered"
    for expected in ("not_null", "unique", "row_count"):
        assert expected in table


def test_steps_and_checks_are_kept_apart():
    table = registry(refresh=True)
    assert table["read_csv"].kind == "step"
    assert table["not_null"].kind == "check"


def test_every_stage_declares_a_description():
    for stage in describe_all():
        assert stage.description, f"{stage.name} has no DESCRIPTION"
        assert stage.description.endswith("."), (
            f"{stage.name}: DESCRIPTION should read as a sentence"
        )


def test_unknown_name_suggests_something_close():
    with pytest.raises(ConfigError) as caught:
        lookup("read_csvv")
    message = str(caught.value)
    assert "read_csvv" in message
    assert "read_csv" in message, "the error should suggest the real name"


def test_unknown_name_with_no_near_match_lists_the_options():
    with pytest.raises(ConfigError) as caught:
        lookup("zzz_nothing_like_this")
    assert "available:" in str(caught.value)
