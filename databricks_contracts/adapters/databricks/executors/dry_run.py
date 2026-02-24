"""
Dry run executor - Prints DDL without executing.

Used for previewing what would be executed without making changes.

Example:
    >>> from databricks_contracts.adapters.databricks.executors import DryRunExecutor
    >>> executor = DryRunExecutor()
    >>> result = executor.execute(statement)  # Prints DDL, doesn't execute
"""

from databricks_contracts.adapters.databricks.executors.base import BaseExecutor
from databricks_contracts.config.logger import get_logger
from databricks_contracts.models.results import ExecutionResult
from databricks_contracts.models.statements import BaseStatement

logger = get_logger(__name__)


class DryRunExecutor(BaseExecutor):
    """
    Dry run executor - prints DDL without executing.

    Use this for previewing what would be executed.
    All operations return success but no actual changes are made.

    Example:
        >>> executor = DryRunExecutor()
        >>>
        >>> # This prints the DDL but doesn't execute it
        >>> result = executor.execute(create_table_stmt)
        >>> print(result.success)  # True
        >>> print(result.dry_run)  # True
        >>>
        >>> # Output in logs:
        >>> # 📋 [DRY RUN] Would execute:
        >>> # CREATE TABLE IF NOT EXISTS...
    """

    def execute(self, statement: BaseStatement) -> ExecutionResult:
        """
        Print DDL statement without executing.

        Args:
            statement: DDL statement model to preview.

        Returns:
            ExecutionResult with success=True and dry_run=True.

        Example:
            >>> result = executor.execute(stmt)
            >>> result.success  # True
            >>> result.dry_run  # True
        """
        logger.info("📋 [DRY RUN] %s", statement.log_message)

        # Log each line of the statement for readability
        for line in statement.statement.split("\n"):
            logger.info("    %s", line)

        return ExecutionResult(
            statement=statement.statement,
            success=True,
            dry_run=True,
        )
