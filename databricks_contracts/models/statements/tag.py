"""
Tag statement model for ALTER TABLE SET TAGS operations.

Each TagStatement carries **one tag** so that a permission failure on a
single tag policy does not prevent the remaining tags from being applied.

Example:
    >>> from databricks_contracts.models.statements import TagStatement
    >>> stmt = TagStatement(
    ...     target="table",
    ...     tags={"portfolio": "Portfolio_1"},
    ...     full_table_name="`cat`.`sch`.`tbl`",
    ... )
    >>> print(stmt.statement)
    ALTER TABLE `cat`.`sch`.`tbl` SET TAGS ('portfolio' = 'Portfolio_1');
"""

from pydantic import Field

from databricks_contracts.models.statements.base import BaseStatement


class TagStatement(BaseStatement):
    """
    Represents a single SET TAGS DDL statement.

    Each instance carries **one tag** (one key-value pair). The builder
    emits one ``TagStatement`` per tag so that failures are isolated —
    a permission error on ``classification`` won't prevent ``portfolio``
    from being applied.

    Can be either table-level or column-level.

    Attributes:
        target: ``"table"`` for table-level, or column name for column-level.
        tags: Single-entry dict ``{tag_name: tag_value}``.
        full_table_name: Fully qualified table name with backticks.

    Example:
        >>> # Table-level tag
        >>> stmt = TagStatement(
        ...     target="table",
        ...     tags={"portfolio": "Portfolio_1"},
        ...     full_table_name="`cat`.`sch`.`tbl`",
        ... )
        >>> print(stmt.statement)
        ALTER TABLE `cat`.`sch`.`tbl` SET TAGS ('portfolio' = 'Portfolio_1');
        >>>
        >>> # Column-level tag
        >>> stmt = TagStatement(
        ...     target="email",
        ...     tags={"privacy": "PII_HIDDEN"},
        ...     full_table_name="`cat`.`sch`.`tbl`",
        ... )
        >>> print(stmt.statement)
        ALTER TABLE `cat`.`sch`.`tbl` ALTER COLUMN `email` SET TAGS ('privacy' = 'PII_HIDDEN');
    """

    target: str = Field(
        ...,
        description="'table' for table-level, or column name",
        examples=["table", "customer_email", "phone_number"],
    )
    tags: dict[str, str] = Field(
        ...,
        description="Tag name to value mapping",
        examples=[{"portfolio": "Portfolio_1", "layer": "Gold"}],
    )
    full_table_name: str = Field(
        ...,
        description="Fully qualified table name with backticks",
        examples=["`catalog`.`schema`.`table`"],
    )

    @property
    def is_table_level(self) -> bool:
        """
        Check if this is a table-level tag statement.

        Returns:
            True if target is "table", False for column-level.

        Example:
            >>> stmt = TagStatement(target="table", ...)
            >>> stmt.is_table_level
            True
        """
        return self.target == "table"

    @property
    def statement(self) -> str:
        """
        Generate the SQL DDL statement.

        Returns:
            Complete ALTER TABLE SET TAGS statement.

        Example:
            >>> stmt.statement
            "ALTER TABLE `cat`.`sch`.`tbl` SET TAGS ('key' = 'value');"
        """

        def _escape_sql_literal(value: str) -> str:
            # Escape for SQL single-quoted literals (portable): ' -> ''
            # Normalize newlines to spaces to avoid multi-line SQL.
            return value.replace("'", "''").replace("\n", " ")

        tags_sql = ", ".join(f"'{key}' = '{_escape_sql_literal(value)}'" for key, value in self.tags.items())

        if self.is_table_level:
            return f"ALTER TABLE {self.full_table_name} SET TAGS ({tags_sql});"

        return f"ALTER TABLE {self.full_table_name} ALTER COLUMN `{self.target}` SET TAGS ({tags_sql});"

    @property
    def log_message(self) -> str:
        """
        Generate a human-readable log message.

        Returns:
            Descriptive message for logging.

        Example:
            >>> stmt.log_message
            "table (portfolio=Portfolio_1, layer=Gold)"
        """
        tags_str = ", ".join(f"{key}={value}" for key, value in self.tags.items())

        if self.is_table_level:
            return f"table ({tags_str})"

        return f"{self.target} ({tags_str})"
