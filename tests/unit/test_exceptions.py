"""Unit tests for custom exceptions."""

from databricks_contracts.exceptions import SparkSQLError, TagAssignmentNotAuthorizedError


class TestSparkSQLError:
    """Tests for SparkSQLError message extraction."""

    def test_extracts_simple_class_and_message(self) -> None:
        raw = "com.databricks.sql.UnauthorizedAccessException: PERMISSION_DENIED: No access"
        err = SparkSQLError(Exception(raw))
        assert str(err) == "UnauthorizedAccessException: PERMISSION_DENIED: No access"
        assert err.original is not None

    def test_strips_py4j_wrapper(self) -> None:
        raw = (
            "An error occurred while calling o398.sql.\n"
            ": com.databricks.sql.UnauthorizedAccessException: PERMISSION_DENIED: test\n"
            "\tat com.databricks.managedcatalog.Foo.bar(Foo.java:42)"
        )
        err = SparkSQLError(Exception(raw))
        assert str(err) == "UnauthorizedAccessException: PERMISSION_DENIED: test"

    def test_returns_line_without_package_prefix(self) -> None:
        raw = "Some simple error message"
        err = SparkSQLError(Exception(raw))
        assert str(err) == "Some simple error message"

    def test_handles_empty_string(self) -> None:
        err = SparkSQLError(Exception(""))
        assert str(err) == ""

    def test_skips_stack_trace_lines(self) -> None:
        raw = (
            "An error occurred while calling o398.sql.\n"
            "at com.databricks.Foo.bar(Foo.java:42)\n"
            "... 20 more\n"
            "com.databricks.AnalysisException: Table not found"
        )
        err = SparkSQLError(Exception(raw))
        assert "AnalysisException" in str(err)


class TestTagAssignmentNotAuthorizedError:
    """Tests for TagAssignmentNotAuthorizedError."""

    def test_stores_tag_key(self) -> None:
        err = TagAssignmentNotAuthorizedError("classification", "PERMISSION_DENIED")
        assert err.tag_key == "classification"

    def test_formats_message(self) -> None:
        err = TagAssignmentNotAuthorizedError("classification", "PERMISSION_DENIED")
        assert "classification" in str(err)
        assert "PERMISSION_DENIED" in str(err)
