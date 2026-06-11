"""Unit tests for TableInspectorService with mocked Spark and SDK backends."""

from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock

import pytest

from databricks_contracts.models.results.query_result import QueryResult
from databricks_contracts.services.databricks.table_inspector import (
    ExistingColumn,
    TableInspectorService,
)

# -- Helpers ------------------------------------------------------------------


class SparkRow(dict):
    """Dict subclass that also supports attribute access, like a real Spark Row."""

    def __getattr__(self, key: str):  # type: ignore[override]
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)


def _make_describe_rows() -> list[SparkRow]:
    """Rows returned by DESCRIBE TABLE EXTENDED for a two-column table."""
    return [
        SparkRow(col_name="id", data_type="string", comment="Primary key"),
        SparkRow(col_name="name", data_type="string", comment="Name"),
        SparkRow(col_name="", data_type="", comment=""),
        SparkRow(col_name="# Detailed Table Information", data_type="", comment=""),
        SparkRow(col_name="Comment", data_type="Test table", comment=""),
    ]


def _make_props_rows() -> list[SparkRow]:
    """Rows returned by SHOW TBLPROPERTIES."""
    return [SparkRow(key="retention_days", value="90")]


def _make_nullable_schema() -> MagicMock:
    """A DataFrame whose .schema.fields carries nullable metadata."""
    field_id = SimpleNamespace(name="id", nullable=False)
    field_name = SimpleNamespace(name="name", nullable=True)
    mock_df = MagicMock()
    mock_df.schema = SimpleNamespace(fields=[field_id, field_name])
    return mock_df


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def mock_spark_executor() -> MagicMock:
    """SparkExecutor mock with a .spark property wired to a mock SparkSession."""
    mock_spark = MagicMock(name="SparkSession")
    mock_executor = MagicMock(name="SparkExecutor")
    type(mock_executor).spark = PropertyMock(return_value=mock_spark)
    return mock_executor


# -- Tests: Spark backend -----------------------------------------------------


class TestTableInspectorViaSpark:
    """Tests for _inspect_via_spark with mocked SparkExecutor."""

    def test_inspect_existing_table(self, mock_spark_executor: MagicMock) -> None:
        spark = mock_spark_executor.spark
        desc_rows = _make_describe_rows()
        props_rows = _make_props_rows()
        nullable_df = _make_nullable_schema()

        def sql_side_effect(sql: str) -> MagicMock:
            result = MagicMock()
            if "DESCRIBE TABLE EXTENDED" in sql:
                result.collect.return_value = desc_rows
            elif "SHOW TBLPROPERTIES" in sql:
                result.collect.return_value = props_rows
            elif "SELECT * FROM" in sql:
                return nullable_df
            return result

        spark.sql.side_effect = sql_side_effect

        inspector = TableInspectorService(spark_executor=mock_spark_executor)
        schema = inspector.inspect("`cat`.`sch`.`tbl`")

        assert schema.exists is True
        assert len(schema.columns) == 2
        assert schema.columns[0].name == "id"
        assert schema.columns[0].nullable is False
        assert schema.columns[1].nullable is True
        assert schema.tblproperties["retention_days"] == "90"

    def test_inspect_nonexistent_table(self, mock_spark_executor: MagicMock) -> None:
        mock_spark_executor.spark.sql.side_effect = Exception("Table not found")

        inspector = TableInspectorService(spark_executor=mock_spark_executor)
        schema = inspector.inspect("`cat`.`sch`.`tbl`")

        assert schema.exists is False


# -- Tests: SDK backend -------------------------------------------------------


class TestTableInspectorViaSDK:
    """Tests for _inspect_via_sdk with mocked DatabricksSQLClient."""

    @pytest.fixture
    def describe_result(self) -> QueryResult:
        return QueryResult(
            success=True,
            rows=[
                {"col_name": "id", "data_type": "string NOT NULL", "comment": "PK"},
                {"col_name": "name", "data_type": "string", "comment": ""},
                {"col_name": "", "data_type": "", "comment": ""},
                {"col_name": "# Detailed Table Information", "data_type": ""},
                {"col_name": "Comment", "data_type": "My table"},
            ],
        )

    @pytest.fixture
    def tblproperties_result(self) -> QueryResult:
        return QueryResult(
            success=True,
            rows=[
                {"key": "retention_days", "value": "90"},
                {"key": "refresh_frequency", "value": "daily"},
            ],
        )

    def test_inspect_existing_table(self, describe_result: QueryResult, tblproperties_result: QueryResult) -> None:
        mock_client = MagicMock()

        def query_side_effect(sql: str) -> QueryResult:
            if "DESCRIBE" in sql:
                return describe_result
            if "TBLPROPERTIES" in sql:
                return tblproperties_result
            return QueryResult(success=False, error="Unknown query")

        mock_client.query.side_effect = query_side_effect

        inspector = TableInspectorService(sql_client=mock_client)
        schema = inspector.inspect("`cat`.`sch`.`tbl`")

        assert schema.exists is True
        assert len(schema.columns) == 2
        assert schema.columns[0].name == "id"
        assert schema.columns[0].nullable is False
        assert schema.columns[1].nullable is True
        assert schema.comment == "My table"
        assert schema.tblproperties["retention_days"] == "90"

    def test_inspect_nonexistent_table(self) -> None:
        mock_client = MagicMock()
        mock_client.query.return_value = QueryResult(success=False, error="Table not found")

        inspector = TableInspectorService(sql_client=mock_client)
        schema = inspector.inspect("`cat`.`sch`.`tbl`")

        assert schema.exists is False

    def test_inspect_connection_exception(self) -> None:
        mock_client = MagicMock()
        mock_client.query.side_effect = Exception("Connection failed")

        inspector = TableInspectorService(sql_client=mock_client)
        schema = inspector.inspect("`cat`.`sch`.`tbl`")

        assert schema.exists is False


# -- Tests: _get_nullable_info_spark ------------------------------------------


class TestTableInspectorGetNullableInfoSpark:
    def test_fallback_on_exception(self) -> None:
        mock_spark = MagicMock()
        mock_spark.sql.side_effect = Exception("No access")

        columns = [ExistingColumn(name="id", type="STRING", nullable=True)]
        result = TableInspectorService._get_nullable_info_spark(mock_spark, "`t`", columns)

        assert len(result) == 1
        assert result[0].nullable is True
