"""Each check, on its own.

A check has two jobs: find the problem, and describe it well enough that
somebody can go and fix the data. The second job is tested here as carefully as
the first.
"""

from __future__ import annotations

import pytest

from sluice.checks import not_null, row_count, unique
from sluice.errors import ConfigError


class TestNotNull:
    def test_clean_data_returns_no_problems(self, rows, ctx):
        assert not_null.check(rows, {"columns": ["customer_id"]}, ctx) == []

    def test_empty_string_counts_as_null(self, ctx):
        rows = [{"email": "a@b.c"}, {"email": ""}]
        problems = not_null.check(rows, {"columns": ["email"]}, ctx)
        assert len(problems) == 1
        assert "row 2" in problems[0]

    def test_whitespace_only_counts_as_null(self, ctx):
        problems = not_null.check([{"email": "   "}], {"columns": ["email"]}, ctx)
        assert len(problems) == 1

    def test_none_counts_as_null(self, ctx):
        problems = not_null.check([{"email": None}], {"columns": ["email"]}, ctx)
        assert len(problems) == 1

    def test_problem_names_the_row_and_the_column(self, ctx):
        problems = not_null.check([{"a": "x"}, {"a": ""}], {"columns": ["a"]}, ctx)
        assert "row 2" in problems[0] and "'a'" in problems[0]

    def test_missing_column_is_itself_a_problem(self, ctx):
        problems = not_null.check([{"a": "x"}], {"columns": ["b"]}, ctx)
        assert len(problems) == 1
        assert "no column" in problems[0]

    def test_a_single_column_name_is_accepted(self, ctx):
        assert not_null.check([{"a": "x"}], {"columns": "a"}, ctx) == []

    def test_missing_option_explains_the_fix(self, rows, ctx):
        with pytest.raises(ConfigError) as caught:
            not_null.check(rows, {}, ctx)
        assert "columns" in str(caught.value)

    def test_does_not_change_the_data(self, ctx):
        rows = [{"a": ""}]
        not_null.check(rows, {"columns": ["a"]}, ctx)
        assert rows == [{"a": ""}], "a check must never modify rows"


class TestUnique:
    def test_distinct_values_pass(self, rows, ctx):
        assert unique.check(rows, {"column": "customer_id"}, ctx) == []

    def test_duplicate_points_at_both_rows(self, ctx):
        rows = [{"id": "1"}, {"id": "2"}, {"id": "1"}]
        problems = unique.check(rows, {"column": "id"}, ctx)
        assert len(problems) == 1
        assert "row 3" in problems[0]
        assert "row 1" in problems[0], "should say where it first appeared"

    def test_several_duplicates_are_all_reported(self, ctx):
        rows = [{"id": "1"}, {"id": "1"}, {"id": "1"}]
        assert len(unique.check(rows, {"column": "id"}, ctx)) == 2

    def test_missing_option_explains_the_fix(self, rows, ctx):
        with pytest.raises(ConfigError, match="column"):
            unique.check(rows, {}, ctx)


class TestRowCount:
    def test_within_range_passes(self, rows, ctx):
        assert row_count.check(rows, {"min": 1, "max": 10}, ctx) == []

    def test_too_few_is_reported_with_both_numbers(self, rows, ctx):
        problems = row_count.check(rows, {"min": 10}, ctx)
        assert len(problems) == 1
        assert "10" in problems[0] and "3" in problems[0]

    def test_too_many_is_reported(self, rows, ctx):
        assert len(row_count.check(rows, {"max": 1}, ctx)) == 1

    def test_empty_input_fails_a_minimum_of_one(self, ctx):
        assert len(row_count.check([], {"min": 1}, ctx)) == 1

    def test_needs_at_least_one_bound(self, rows, ctx):
        with pytest.raises(ConfigError):
            row_count.check(rows, {}, ctx)
