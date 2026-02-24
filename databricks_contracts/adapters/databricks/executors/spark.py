"""
Spark executor - Executes DDL via SparkSession.

Used for actual execution in Databricks or local Spark environments.

Example:
    >>> from databricks_contracts.adapters.databricks.executors import SparkExecutor
    >>> executor = SparkExecutor()
    >>> result = executor.execute(statement)  # Actually executes the DDL
"""

from typing import Any, Optional

from databricks_contracts.adapters.databricks.executors.base import BaseExecutor
from databricks_contracts.config.logger import get_logger
from databricks_contracts.exceptions import ExecutionError, SparkSQLError
from databricks_contracts.models.results import ExecutionResult
from databricks_contracts.models.statements import BaseStatement

logger = get_logger(__name__)


class SparkExecutor(BaseExecutor):
    """
    Spark executor - executes DDL via SparkSession.

    Works in both Databricks (uses existing session) and locally
    (creates new session if PySpark is available).

    Attributes:
        spark: SparkSession instance (lazy initialized).

    Example:
        >>> # Default - auto-detect/create SparkSession
        >>> executor = SparkExecutor()
        >>>
        >>> # With explicit SparkSession
        >>> executor = SparkExecutor(spark=my_spark_session)
        >>>
        >>> # Execute DDL
        >>> result = executor.execute(create_table_stmt)
        >>> if result.success:
        ...     print("Table created!")
    """

    def __init__(self, spark: Optional[Any] = None) -> None:
        """
        Initialize the Spark executor.

        Args:
            spark: Optional SparkSession. If None, will try to get/create one.

        Example:
            >>> executor = SparkExecutor()  # Auto-detect
            >>> executor = SparkExecutor(spark=existing_session)  # Explicit
        """
        self._spark = spark

    @property
    def spark(self) -> Any:
        """
        Get or create SparkSession.

        Returns:
            SparkSession instance.

        Raises:
            ExecutionError: If PySpark is not available.

        Example:
            >>> session = executor.spark
            >>> session.sql("SELECT 1").show()
        """
        if self._spark is None:
            self._spark = self._get_or_create_spark()
        return self._spark

    def _get_or_create_spark(self) -> Any:
        """
        Get existing or create new SparkSession.

        Returns:
            SparkSession instance.

        Raises:
            ExecutionError: If PySpark is not available.
        """
        try:
            from pyspark.sql import SparkSession

            return SparkSession.builder.getOrCreate()
        except ImportError:
            raise ExecutionError("PySpark not available. Install pyspark or run in Databricks environment.")

    def execute(self, statement: BaseStatement) -> ExecutionResult:
        """
        Execute a DDL statement via Spark SQL.

        On failure, the raw Py4J / JVM exception is wrapped in a
        :class:`~databricks_contracts.exceptions.SparkSQLError` which
        strips the Java stack trace and keeps only the human-readable
        message (e.g. ``UnauthorizedAccessException: PERMISSION_DENIED: …``).

        Args:
            statement: DDL statement model to execute.

        Returns:
            ExecutionResult with success status and a clean error message.

        Example:
            >>> result = executor.execute(create_table_stmt)
            >>> if not result.success:
            ...     print(result.error)  # clean, one-line message
        """
        try:
            logger.info("⏳ %s...", statement.log_message)
            self.spark.sql(statement.statement)
            logger.info("✅ Done: %s", statement.log_message)

            return ExecutionResult(
                statement=statement.statement,
                success=True,
            )
        except Exception as e:
            spark_err = SparkSQLError(e)
            logger.error("❌ Failed: %s - %s", statement.log_message, spark_err)
            return ExecutionResult(
                statement=statement.statement,
                success=False,
                error=str(spark_err),
            )

    def is_available(self) -> bool:
        """
        Check if Spark is available.

        Returns:
            True if SparkSession can be created, False otherwise.

        Example:
            >>> if executor.is_available():
            ...     executor.execute(stmt)
            ... else:
            ...     print("Spark not available")
        """
        try:
            _ = self.spark
            return True
        except ExecutionError:
            return False
