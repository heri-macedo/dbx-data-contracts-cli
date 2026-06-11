"""Unit tests for DatabricksSQLClient."""

from types import SimpleNamespace

from databricks_contracts.adapters.databricks.sql_client import DatabricksSQLClient

# -- Helpers ------------------------------------------------------------------


def _make_column(name: str) -> SimpleNamespace:
    """Create a fake SDK column descriptor."""
    return SimpleNamespace(name=name)


def _make_statement_result(
    column_names: list[str] | None = None,
    data_rows: list[list[str]] | None = None,
) -> SimpleNamespace:
    """Build a fake Statement Execution API result.

    Mirrors the nested structure returned by WorkspaceClient.statement_execution.
    """
    if column_names is None:
        return SimpleNamespace(manifest=None, result=None)

    columns = [_make_column(n) for n in column_names]
    schema = SimpleNamespace(columns=columns)
    manifest = SimpleNamespace(schema=schema)
    data = SimpleNamespace(data_array=data_rows)
    return SimpleNamespace(manifest=manifest, result=data)


# -- Tests --------------------------------------------------------------------


class TestDatabricksSQLClientParseResult:
    """Tests for _parse_result static method."""

    def test_parse_basic_result(self) -> None:
        result = _make_statement_result(
            column_names=["id", "name"],
            data_rows=[["1", "Alice"], ["2", "Bob"]],
        )

        rows = DatabricksSQLClient._parse_result(result)

        assert len(rows) == 2
        assert rows[0] == {"id": "1", "name": "Alice"}
        assert rows[1] == {"id": "2", "name": "Bob"}

    def test_parse_empty_data_array(self) -> None:
        result = _make_statement_result(column_names=[], data_rows=None)

        rows = DatabricksSQLClient._parse_result(result)

        assert rows == []

    def test_parse_no_manifest(self) -> None:
        result = SimpleNamespace(other="value")

        rows = DatabricksSQLClient._parse_result(result)

        assert rows == []

    def test_parse_null_manifest_and_data(self) -> None:
        result = _make_statement_result()  # both None

        rows = DatabricksSQLClient._parse_result(result)

        assert rows == []

    def test_parse_no_schema_columns(self) -> None:
        manifest = SimpleNamespace(schema=SimpleNamespace(columns=None))
        data = SimpleNamespace(data_array=[["1"]])
        result = SimpleNamespace(manifest=manifest, result=data)

        rows = DatabricksSQLClient._parse_result(result)

        assert rows == [{}]

    def test_parse_row_shorter_than_columns(self) -> None:
        result = _make_statement_result(
            column_names=["id", "name"],
            data_rows=[["1"]],  # only 1 value for 2 columns
        )

        rows = DatabricksSQLClient._parse_result(result)

        assert len(rows) == 1
        assert rows[0] == {"id": "1", "name": None}
