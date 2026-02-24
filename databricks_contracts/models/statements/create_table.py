"""
Create table statement model.

Represents a CREATE TABLE DDL statement for Unity Catalog.

Example:
    >>> from databricks_contracts.models.statements import CreateTableStatement
    >>> stmt = CreateTableStatement(
    ...     full_table_name="`cat`.`sch`.`tbl`",
    ...     ddl="CREATE TABLE IF NOT EXISTS `cat`.`sch`.`tbl` (...)",
    ... )
    >>> print(stmt.statement)
"""

from pydantic import Field

from databricks_contracts.models.statements.base import BaseStatement


class CreateTableStatement(BaseStatement):
    """
    Represents a CREATE TABLE DDL statement.

    Immutable model containing the complete DDL for table creation.

    Attributes:
        full_table_name: Fully qualified table name with backticks.
        ddl: Complete CREATE TABLE DDL string.

    Example:
        >>> stmt = CreateTableStatement(
        ...     full_table_name="`catalog`.`schema`.`my_table`",
        ...     ddl="CREATE TABLE IF NOT EXISTS `catalog`.`schema`.`my_table` (id STRING)",
        ... )
        >>> print(stmt.statement)
        CREATE TABLE IF NOT EXISTS `catalog`.`schema`.`my_table` (id STRING)
        >>> print(stmt.log_message)
        Creating table `catalog`.`schema`.`my_table`
    """

    full_table_name: str = Field(
        ...,
        description="Fully qualified table name with backticks",
        examples=["`catalog`.`schema`.`table`"],
    )
    ddl: str = Field(
        ...,
        description="Complete CREATE TABLE DDL",
    )

    @property
    def statement(self) -> str:
        """
        Return the DDL statement.

        Returns:
            The complete CREATE TABLE DDL string.

        Example:
            >>> stmt.statement
            "CREATE TABLE IF NOT EXISTS..."
        """
        return self.ddl

    @property
    def log_message(self) -> str:
        """
        Generate log message for table creation.

        Returns:
            Human-readable message describing the operation.

        Example:
            >>> stmt.log_message
            "Creating table `catalog`.`schema`.`table`"
        """
        return f"Creating table {self.full_table_name}"
