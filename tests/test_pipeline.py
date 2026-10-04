"""Loading and running a whole pipeline.

The loader's job is to fail *before* any data is touched. A pipeline that reads
four million rows and then discovers stage six is misspelled has wasted
everybody's time, so the mistakes that can be caught up front are caught here.
"""

from __future__ import annotations

import pytest

from sluice import pipeline as pipeline_module
from sluice.context import RunContext
from sluice.errors import CheckFailed, ConfigError, StepError


def write(tmp_path, text, name="p.toml"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


class TestLoad:
    def test_loads_a_valid_file(self, tmp_path, csv_file):
        path = write(
            tmp_path,
            f"""
name = "demo"
[[stage]]
use  = "read_csv"
path = "{csv_file}"
""",
        )
        spec = pipeline_module.load(path)
        assert spec.name == "demo"
        assert len(spec.stages) == 1

    def test_missing_file_is_a_config_error(self, tmp_path):
        with pytest.raises(ConfigError, match="no pipeline file"):
            pipeline_module.load(tmp_path / "nope.toml")

    def test_invalid_toml_says_it_is_invalid_toml(self, tmp_path):
        path = write(tmp_path, "name = [unclosed")
        with pytest.raises(ConfigError, match="not valid TOML"):
            pipeline_module.load(path)

    def test_missing_name_explains_the_fix(self, tmp_path):
        path = write(tmp_path, '[[stage]]\nuse = "read_csv"\n')
        with pytest.raises(ConfigError) as caught:
            pipeline_module.load(path)
        assert "name" in str(caught.value)

    def test_no_stages_is_refused(self, tmp_path):
        path = write(tmp_path, 'name = "x"\n')
        with pytest.raises(ConfigError, match="no stages"):
            pipeline_module.load(path)

    def test_single_bracket_stage_is_caught_with_a_hint(self, tmp_path):
        path = write(tmp_path, 'name = "x"\n[stage]\nuse = "read_csv"\n')
        with pytest.raises(ConfigError) as caught:
            pipeline_module.load(path)
        assert "[[stage]]" in str(caught.value)

    def test_stage_without_use_is_refused(self, tmp_path):
        path = write(tmp_path, 'name = "x"\n[[stage]]\npath = "a.csv"\n')
        with pytest.raises(ConfigError, match="no 'use'"):
            pipeline_module.load(path)

    def test_unknown_stage_fails_at_load_not_at_run(self, tmp_path):
        path = write(tmp_path, 'name = "x"\n[[stage]]\nuse = "no_such_step"\n')
        with pytest.raises(ConfigError):
            pipeline_module.load(path)


class TestRun:
    def test_stages_run_in_order(self, tmp_path, csv_file):
        path = write(
            tmp_path,
            f"""
name = "demo"
[[stage]]
use  = "read_csv"
path = "{csv_file}"
[[stage]]
use     = "rename_columns"
mapping = {{ cust_id = "customer_id" }}
[[stage]]
use    = "filter_rows"
column = "status"
equals = "active"
""",
        )
        out = pipeline_module.run(
            pipeline_module.load(path), RunContext(pipeline="demo", _stream=_sink())
        )
        assert len(out) == 2
        assert "customer_id" in out[0]

    def test_a_failing_check_stops_the_pipeline(self, tmp_path, csv_file):
        path = write(
            tmp_path,
            f"""
name = "demo"
[[stage]]
use  = "read_csv"
path = "{csv_file}"
[[stage]]
use = "row_count"
min = 999
[[stage]]
use     = "rename_columns"
mapping = {{ cust_id = "x" }}
""",
        )
        with pytest.raises(CheckFailed) as caught:
            pipeline_module.run(
                pipeline_module.load(path), RunContext(pipeline="demo", _stream=_sink())
            )
        assert "row_count" in str(caught.value)

    def test_check_failure_lists_what_was_wrong(self, tmp_path, csv_file):
        path = write(
            tmp_path,
            f"""
name = "demo"
[[stage]]
use  = "read_csv"
path = "{csv_file}"
[[stage]]
use     = "not_null"
columns = ["nope"]
""",
        )
        with pytest.raises(CheckFailed) as caught:
            pipeline_module.run(
                pipeline_module.load(path), RunContext(pipeline="demo", _stream=_sink())
            )
        assert "row 1" in str(caught.value)

    def test_an_unexpected_error_still_names_the_stage(self, tmp_path, csv_file, monkeypatch):
        from sluice.steps import rename_columns

        def explode(rows, options, ctx):
            raise ValueError("something nobody predicted")

        monkeypatch.setattr(rename_columns, "run", explode)
        # The registry caches the function object it found at import time, so a
        # patched module attribute is not seen until the registry is rebuilt.
        from sluice import registry as registry_module

        registry_module.registry(refresh=True)

        path = write(
            tmp_path,
            f"""
name = "demo"
[[stage]]
use  = "read_csv"
path = "{csv_file}"
[[stage]]
use     = "rename_columns"
mapping = {{ a = "b" }}
""",
        )
        with pytest.raises(StepError) as caught:
            pipeline_module.run(
                pipeline_module.load(path), RunContext(pipeline="demo", _stream=_sink())
            )
        message = str(caught.value)
        assert "rename_columns" in message
        assert "ValueError" in message

    def test_counters_record_what_happened(self, tmp_path, csv_file):
        path = write(
            tmp_path,
            f"""
name = "demo"
[[stage]]
use  = "read_csv"
path = "{csv_file}"
""",
        )
        ctx = RunContext(pipeline="demo", _stream=_sink())
        pipeline_module.run(pipeline_module.load(path), ctx)
        assert ctx.counters["rows_read"] == 3


@pytest.fixture(autouse=True)
def _reset_registry_cache():
    """Any test that patches a stage must not leak into the next one."""
    yield
    from sluice import registry as registry_module

    registry_module.registry(refresh=True)


def _sink():
    import io

    return io.StringIO()
