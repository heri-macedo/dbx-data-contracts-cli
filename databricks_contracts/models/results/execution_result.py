"""
Execution result model for SQL statement execution.

Represents the result of executing a single SQL statement.

Example:
    >>> from databricks_contracts.models.results import ExecutionResult
    >>> result = ExecutionResult(
    ...     statement="CREATE TABLE...",
    ...     success=True,
    ... )
"""

from typing import Optional

from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    """
    Result of executing a SQL statement.

    Immutable model containing the outcome of a single DDL execution.

    Attributes:
        statement: The SQL statement that was executed.
        success: Whether the execution succeeded.
        error: Error message if execution failed.
        dry_run: Whether this was a dry run (not actually executed).

    Example:
        >>> # Successful execution
        >>> result = ExecutionResult(
        ...     statement="CREATE TABLE catalog.schema.table...",
        ...     success=True,
        ... )
        >>>
        >>> # Dry run
        >>> result = ExecutionResult(
        ...     statement="CREATE TABLE...",
        ...     success=True,
        ...     dry_run=True,
        ... )
        >>>
        >>> # Failed execution
        >>> result = ExecutionResult(
        ...     statement="CREATE TABLE...",
        ...     success=False,
        ...     error="Table already exists",
        ... )
    """

    model_config = {"frozen": True}

    statement: str = Field(
        ...,
        description="SQL statement executed",
    )
    success: bool = Field(
        ...,
        description="Whether execution succeeded",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed",
    )
    dry_run: bool = Field(
        default=False,
        description="Whether this was a dry run",
    )
