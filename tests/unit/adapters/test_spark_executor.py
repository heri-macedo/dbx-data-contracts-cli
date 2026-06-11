"""Unit tests for SparkExecutor with mocked SparkSession."""

from unittest.mock import MagicMock

import pytest

from databricks_contracts.adapters.databricks.executors.spark import SparkExecutor
from databricks_contracts.exceptions import ExecutionError
from databricks_contracts.models.statements.create_table import CreateTableStatement

# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def sample_statement() -> CreateTableStatement:
    return CreateTableStatement(
        full_table_name="`cat`.`sch`.`tbl`",
        ddl="CREATE TABLE IF NOT EXISTS `cat`.`sch`.`tbl` (id STRING);",
    )


@pytest.fixture
def mock_spark() -> MagicMock:
    return MagicMock(name="SparkSession")


@pytest.fixture
def executor_with_spark(mock_spark: MagicMock) -> SparkExecutor:
    return SparkExecutor(spark=mock_spark)


@pytest.fixture
def executor_without_spark() -> SparkExecutor:
    return SparkExecutor(spark=None)


def _block_pyspark_import(monkeypatch: pytest.MonkeyPatch) -> None:
    """Monkey-patch builtins.__import__ so `import pyspark.sql` raises ImportError."""
    import builtins

    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "pyspark.sql":
            raise ImportError("No module named 'pyspark'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)


# -- Tests --------------------------------------------------------------------


class TestSparkExecutorExecute:
    def test_execute_success(
        self,
        executor_with_spark: SparkExecutor,
        mock_spark: MagicMock,
        sample_statement: CreateTableStatement,
    ) -> None:
        result = executor_with_spark.execute(sample_statement)

        assert result.success is True
        mock_spark.sql.assert_called_once_with(sample_statement.statement)

    def test_execute_failure_wraps_error(
        self,
        executor_with_spark: SparkExecutor,
        mock_spark: MagicMock,
        sample_statement: CreateTableStatement,
    ) -> None:
        mock_spark.sql.side_effect = Exception("PERMISSION_DENIED: User does not have access")

        result = executor_with_spark.execute(sample_statement)

        assert result.success is False
        assert result.error is not None


class TestSparkExecutorSparkProperty:
    def test_spark_returns_provided_session(self, mock_spark: MagicMock) -> None:
        executor = SparkExecutor(spark=mock_spark)
        assert executor.spark is mock_spark

    def test_spark_raises_without_pyspark(
        self, executor_without_spark: SparkExecutor, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _block_pyspark_import(monkeypatch)

        with pytest.raises(ExecutionError, match="PySpark not available"):
            _ = executor_without_spark.spark


class TestSparkExecutorIsAvailable:
    def test_is_available_true(self, executor_with_spark: SparkExecutor) -> None:
        assert executor_with_spark.is_available() is True

    def test_is_available_false_when_no_spark(
        self, executor_without_spark: SparkExecutor, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _block_pyspark_import(monkeypatch)

        assert executor_without_spark.is_available() is False
