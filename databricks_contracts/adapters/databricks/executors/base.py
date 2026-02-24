"""
Base executor interface for DDL operations.

Defines the contract for all DDL execution strategies.

Example:
    >>> from databricks_contracts.adapters.databricks.executors import BaseExecutor
    >>>
    >>> class MyExecutor(BaseExecutor):
    ...     def execute(self, statement):
    ...         # Custom execution logic
    ...         pass
"""

from abc import ABC, abstractmethod

from databricks_contracts.models.results import ExecutionResult
from databricks_contracts.models.statements import BaseStatement


class BaseExecutor(ABC):
    """
    Abstract base class for DDL executors.

    Defines the interface for executing DDL statements.
    Implementations provide different strategies (Spark, DryRun, etc.).

    Example:
        >>> class CustomExecutor(BaseExecutor):
        ...     def execute(self, statement: BaseStatement) -> ExecutionResult:
        ...         # Custom execution logic
        ...         return ExecutionResult(statement=statement.statement, success=True)
    """

    @abstractmethod
    def execute(self, statement: BaseStatement) -> ExecutionResult:
        """
        Execute a single DDL statement.

        Args:
            statement: DDL statement model to execute.

        Returns:
            ExecutionResult with success status and any error.

        Example:
            >>> result = executor.execute(create_table_stmt)
            >>> if result.success:
            ...     print("Executed successfully")
        """
        pass

    def execute_batch(self, statements: list[BaseStatement]) -> list[ExecutionResult]:
        """
        Execute multiple DDL statements.

        Default implementation executes statements sequentially.
        Subclasses can override for batch optimization.

        Args:
            statements: List of DDL statement models.

        Returns:
            List of ExecutionResult for each statement.

        Example:
            >>> results = executor.execute_batch([stmt1, stmt2, stmt3])
            >>> success_count = sum(1 for r in results if r.success)
        """
        return [self.execute(stmt) for stmt in statements]
