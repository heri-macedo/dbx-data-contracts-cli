"""
Statement build result model for DDL generation.

Represents the structured output from BuilderService.

Example:
    >>> from databricks_contracts.models.results import StatementBuildResult
    >>> result = builder.build(contract)
    >>> print(result.create_ddl)
"""

from typing import Optional

from pydantic import BaseModel, Field

from databricks_contracts.models.statements import (
    BaseStatement,
    CreateTableStatement,
    GrantStatement,
    TagStatement,
)
from databricks_contracts.models.statements.constraint import AddConstraintStatement


class StatementBuildResult(BaseModel):
    """
    Result of building DDL statements from a contract.

    Structured container separating CREATE TABLE, SET TAGS, and GRANT statements.

    Attributes:
        create_table: The CREATE TABLE statement.
        tags: List of SET TAGS statements.
        grant: GRANT statement for Service Principal.

    Example:
        >>> result = builder.build(contract)
        >>> print(result.create_ddl)
        >>> print(result.tags_ddl)
        >>> executor.execute_batch(result.all_statements)
    """

    model_config = {"frozen": True}

    create_table: CreateTableStatement = Field(
        ...,
        description="CREATE TABLE statement",
    )
    tags: list[TagStatement] = Field(
        default_factory=list,
        description="SET TAGS statements",
    )
    constraints: list[AddConstraintStatement] = Field(
        default_factory=list,
        description="ADD CONSTRAINT statements for CHECK constraints",
    )
    grant: Optional[GrantStatement] = Field(
        default=None,
        description="GRANT MODIFY statement for Service Principal (None if WORKFLOW_SP_ID not set)",
    )

    @property
    def all_statements(self) -> list[BaseStatement]:
        """
        All statements in execution order.

        Returns:
            List with CREATE TABLE, SET TAGS, and GRANT statements.

        Example:
            >>> executor.execute_batch(result.all_statements)
        """
        stmts: list[BaseStatement] = [self.create_table, *self.tags, *self.constraints]
        if self.grant is not None:
            stmts.append(self.grant)
        return stmts

    @property
    def create_ddl(self) -> str:
        """
        CREATE TABLE DDL string.

        Returns:
            The CREATE TABLE DDL statement.

        Example:
            >>> print(result.create_ddl)
            "CREATE TABLE IF NOT EXISTS..."
        """
        return self.create_table.statement

    @property
    def tags_ddl(self) -> str:
        """
        All SET TAGS DDL as single string.

        Returns:
            Newline-separated SET TAGS statements.

        Example:
            >>> print(result.tags_ddl)
            "ALTER TABLE ... SET TAGS...\\nALTER TABLE..."
        """
        return "\n".join(t.statement for t in self.tags)


class EvolutionBuildResult(BaseModel):
    """Result of building ALTER statements for schema evolution."""

    model_config = {"frozen": True}

    alter_statements: list[BaseStatement] = Field(
        default_factory=list,
        description="ALTER statements for safe schema changes",
    )
    tag_statements: list[TagStatement] = Field(
        default_factory=list,
        description="SET TAGS statements (idempotent, always applied)",
    )
    constraint_statements: list[BaseStatement] = Field(
        default_factory=list,
        description="ADD/DROP CONSTRAINT statements",
    )
    grant: Optional[GrantStatement] = Field(
        default=None,
        description="GRANT MODIFY statement (None if WORKFLOW_SP_ID not set)",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Warnings for unsafe changes that were skipped",
    )

    @property
    def has_changes(self) -> bool:
        """Whether there are any changes to apply."""
        return bool(self.alter_statements or self.tag_statements or self.constraint_statements or self.grant)

    @property
    def all_statements(self) -> list[BaseStatement]:
        """All statements in execution order."""
        stmts: list[BaseStatement] = [*self.alter_statements, *self.tag_statements, *self.constraint_statements]
        if self.grant is not None:
            stmts.append(self.grant)
        return stmts
