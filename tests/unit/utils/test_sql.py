"""Unit tests for escape_sql_literal utility."""

from databricks_contracts.utils.sql import escape_sql_literal


class TestEscapeSqlLiteral:
    """Tests for the shared SQL escaping utility."""

    def test_escapes_single_quotes(self) -> None:
        assert escape_sql_literal("it's") == "it''s"

    def test_escapes_multiple_single_quotes(self) -> None:
        assert escape_sql_literal("it's a 'test'") == "it''s a ''test''"

    def test_normalizes_newlines_to_spaces(self) -> None:
        assert escape_sql_literal("line1\nline2") == "line1 line2"

    def test_handles_both_quotes_and_newlines(self) -> None:
        assert escape_sql_literal("it's\nnew") == "it''s new"

    def test_empty_string(self) -> None:
        assert escape_sql_literal("") == ""

    def test_no_special_chars(self) -> None:
        assert escape_sql_literal("hello world") == "hello world"
