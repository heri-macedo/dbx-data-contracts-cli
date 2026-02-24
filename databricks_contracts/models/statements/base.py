"""
Base statement model for DDL operations.

Abstract base class for all DDL statement types.

Example:
    >>> from databricks_contracts.models.statements import BaseStatement
    >>> class MyStatement(BaseStatement):
    ...     @property
    ...     def statement(self) -> str:
    ...         return "SELECT 1"
    ...     @property
    ...     def log_message(self) -> str:
    ...         return "Executing query"
"""

from abc import abstractmethod

from pydantic import BaseModel


class BaseStatement(BaseModel):
    """
    Abstract base for all DDL statement models.

    All DDL statements must provide:
    - statement: The SQL DDL string to execute.
    - log_message: Human-readable description for logging.

    Attributes:
        None (abstract base class).

    Example:
        >>> class CreateStatement(BaseStatement):
        ...     table_name: str
        ...
        ...     @property
        ...     def statement(self) -> str:
        ...         return f"CREATE TABLE {self.table_name}"
        ...
        ...     @property
        ...     def log_message(self) -> str:
        ...         return f"Creating table {self.table_name}"
    """

    model_config = {"frozen": True}

    @property
    @abstractmethod
    def statement(self) -> str:
        """
        Generate the SQL DDL statement.

        Returns:
            SQL DDL string ready to execute.

        Example:
            >>> stmt.statement
            "CREATE TABLE IF NOT EXISTS catalog.schema.table..."
        """
        ...

    @property
    @abstractmethod
    def log_message(self) -> str:
        """
        Generate a human-readable log message.

        Returns:
            Descriptive message for logging.

        Example:
            >>> stmt.log_message
            "Creating table catalog.schema.table"
        """
        ...
