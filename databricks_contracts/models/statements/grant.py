"""
Grant statement model for GRANT operations.

Represents a GRANT DDL statement for Unity Catalog.

Example:
    >>> from databricks_contracts.models.statements import GrantStatement
    >>> stmt = GrantStatement(
    ...     full_table_name="`cat`.`sch`.`tbl`",
    ...     principal="6eb173d7-a50a-443f-9edd-cddb96f77e62",
    ... )
    >>> print(stmt.statement)
"""

from pydantic import Field

from databricks_contracts.models.statements.base import BaseStatement


class GrantStatement(BaseStatement):
    """
    Represents a GRANT MODIFY DDL statement.

    Grants MODIFY permission on a table to a Service Principal.

    Attributes:
        full_table_name: Fully qualified table name with backticks.
        principal: Service Principal ID to grant permission to.

    Example:
        >>> stmt = GrantStatement(
        ...     full_table_name="`catalog`.`schema`.`my_table`",
        ...     principal="6eb173d7-a50a-443f-9edd-cddb96f77e62",
        ... )
        >>> print(stmt.statement)
        GRANT MODIFY ON TABLE `catalog`.`schema`.`my_table` TO `SERVICE_PRINCIPAL_ID`;
        >>> print(stmt.log_message)
        Granting MODIFY to SERVICE_PRINCIPAL_ID on `catalog`.`schema`.`my_table`
    """

    full_table_name: str = Field(
        ...,
        description="Fully qualified table name with backticks",
        examples=["`catalog`.`schema`.`table`"],
    )
    principal: str = Field(
        ...,
        description="Service Principal ID to grant permission to",
        examples=["6eb173d7-a50a-443f-9edd-cddb96f77e62"],
    )

    @property
    def statement(self) -> str:
        """
        Return the GRANT DDL statement.

        Returns:
            The complete GRANT MODIFY DDL string.

        Example:
            >>> stmt.statement
            "GRANT MODIFY ON TABLE `catalog`.`schema`.`table` TO `<SP_ID>`;"
        """
        return f"GRANT MODIFY ON TABLE {self.full_table_name} TO `{self.principal}`;"

    @property
    def log_message(self) -> str:
        """
        Generate log message for grant operation.

        Returns:
            Human-readable message describing the operation.

        Example:
            >>> stmt.log_message
            "Granting MODIFY to <SP_ID> on `catalog`.`schema`.`table`"
        """
        return f"Granting MODIFY to {self.principal} on {self.full_table_name}"
