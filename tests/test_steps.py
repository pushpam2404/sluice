"""Each step, on its own.

These assert on the *message* as well as the failure, because an error that
does not say which column or which row is barely better than no error.
"""

from __future__ import annotations

import sqlite3

import pytest

from sluice.errors import StepError
from sluice.steps import filter_rows, read_csv, read_json, rename_columns, write_sqlite


class TestReadCsv:
    def test_reads_every_row(self, csv_file, ctx):
        out = read_csv.run([], {"path": str(csv_file)}, ctx)
        assert len(out) == 3
        assert out[0]["full_name"] == "Asha"

    def test_counts_what_it_read(self, csv_file, ctx):
        read_csv.run([], {"path": str(csv_file)}, ctx)
        assert ctx.counters["rows_read"] == 3

    def test_missing_path_option_says_so(self, ctx):
        with pytest.raises(StepError, match="no 'path' given"):
            read_csv.run([], {}, ctx)

    def test_missing_file_names_the_file(self, ctx, tmp_path):
        missing = tmp_path / "nope.csv"
        with pytest.raises(StepError) as caught:
            read_csv.run([], {"path": str(missing)}, ctx)
        assert "nope.csv" in str(caught.value)

    def test_empty_file_is_an_error_not_an_empty_list(self, tmp_path, ctx):
        empty = tmp_path / "empty.csv"
        empty.write_text("", encoding="utf-8")
        with pytest.raises(StepError, match="empty"):
            read_csv.run([], {"path": str(empty)}, ctx)


class TestReadJson:
    def test_reads_a_list_of_objects(self, tmp_path, ctx):
        path = tmp_path / "x.json"
        path.write_text('[{"a": 1}, {"a": 2}]', encoding="utf-8")
        assert len(read_json.run([], {"path": str(path)}, ctx)) == 2

    def test_bad_json_reports_the_line(self, tmp_path, ctx):
        path = tmp_path / "bad.json"
        path.write_text('[{"a": 1},', encoding="utf-8")
        with pytest.raises(StepError) as caught:
            read_json.run([], {"path": str(path)}, ctx)
        assert "line" in str(caught.value)

    def test_object_without_key_option_explains_the_fix(self, tmp_path, ctx):
        path = tmp_path / "obj.json"
        path.write_text('{"records": [{"a": 1}]}', encoding="utf-8")
        with pytest.raises(StepError) as caught:
            read_json.run([], {"path": str(path)}, ctx)
        assert "key" in str(caught.value)

    def test_object_with_key_option_works(self, tmp_path, ctx):
        path = tmp_path / "obj.json"
        path.write_text('{"records": [{"a": 1}]}', encoding="utf-8")
        out = read_json.run([], {"path": str(path), "key": "records"}, ctx)
        assert out == [{"a": 1}]


class TestRenameColumns:
    def test_renames_only_what_was_asked(self, rows, ctx):
        out = rename_columns.run(rows, {"mapping": {"name": "full_name"}}, ctx)
        assert "full_name" in out[0]
        assert "name" not in out[0]
        assert out[0]["customer_id"] == "1"

    def test_renaming_an_absent_column_fails_loudly(self, rows, ctx):
        with pytest.raises(StepError) as caught:
            rename_columns.run(rows, {"mapping": {"nope": "x"}}, ctx)
        message = str(caught.value)
        assert "nope" in message
        assert "customer_id" in message, "should list what columns do exist"

    def test_does_not_mutate_the_rows_it_was_given(self, rows, ctx):
        rename_columns.run(rows, {"mapping": {"name": "full_name"}}, ctx)
        assert "name" in rows[0], "a step must not change its input in place"


class TestFilterRows:
    def test_equals_keeps_matching(self, rows, ctx):
        out = filter_rows.run(rows, {"column": "status", "equals": "active"}, ctx)
        assert len(out) == 2

    def test_not_equals_drops_matching(self, rows, ctx):
        out = filter_rows.run(rows, {"column": "status", "not_equals": "active"}, ctx)
        assert len(out) == 1

    def test_counts_what_it_dropped(self, rows, ctx):
        filter_rows.run(rows, {"column": "status", "equals": "active"}, ctx)
        assert ctx.counters["rows_filtered_out"] == 1

    def test_unknown_column_lists_the_real_ones(self, rows, ctx):
        with pytest.raises(StepError) as caught:
            filter_rows.run(rows, {"column": "nope", "equals": "x"}, ctx)
        assert "status" in str(caught.value)

    def test_needs_a_comparison(self, rows, ctx):
        with pytest.raises(StepError, match="equals"):
            filter_rows.run(rows, {"column": "status"}, ctx)


class TestWriteSqlite:
    def test_writes_every_row(self, rows, ctx, tmp_path):
        db = tmp_path / "w.db"
        write_sqlite.run(rows, {"database": str(db), "table": "people"}, ctx)
        with sqlite3.connect(db) as conn:
            assert conn.execute("SELECT COUNT(*) FROM people").fetchone()[0] == 3

    def test_replaces_rather_than_appending(self, rows, ctx, tmp_path):
        db = tmp_path / "w.db"
        opts = {"database": str(db), "table": "people"}
        write_sqlite.run(rows, opts, ctx)
        write_sqlite.run(rows, opts, ctx)
        with sqlite3.connect(db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        assert count == 3, "running twice should not double the data"

    def test_dry_run_writes_nothing(self, rows, ctx, tmp_path):
        db = tmp_path / "w.db"
        ctx.dry_run = True
        write_sqlite.run(rows, {"database": str(db), "table": "people"}, ctx)
        assert not db.exists()

    def test_ragged_rows_are_refused(self, ctx, tmp_path):
        ragged = [{"a": 1, "b": 2}, {"a": 3}]
        with pytest.raises(StepError) as caught:
            write_sqlite.run(ragged, {"database": str(tmp_path / "w.db"), "table": "t"}, ctx)
        assert "row 2" in str(caught.value)

    def test_unsafe_table_name_is_refused(self, rows, ctx, tmp_path):
        with pytest.raises(StepError, match="safe table name"):
            write_sqlite.run(
                rows, {"database": str(tmp_path / "w.db"), "table": "people; DROP TABLE x"}, ctx
            )

    def test_empty_input_warns_rather_than_silently_doing_nothing(self, ctx, tmp_path):
        write_sqlite.run([], {"database": str(tmp_path / "w.db"), "table": "t"}, ctx)
        assert "0 rows" in ctx.stream.getvalue()
