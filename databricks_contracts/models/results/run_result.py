"""
Run result model for contract apply operations.

Represents the result of applying a contract to Unity Catalog.

Example:
    >>> from databricks_contracts.models.results import RunResult
    >>> result = RunResult(
    ...     contract_name="orders_v1",
    ...     success=True,
    ...     create_ddl="CREATE TABLE...",
    ... )
"""

from typing import Optional

from pydantic import BaseModel, Field


class RunResult(BaseModel):
    """
    Result of applying a contract to Unity Catalog.

    ``success`` is ``True`` when the CREATE TABLE statement succeeds.
    Tag and grant failures are **non-fatal** and collected in ``warnings``.

    Attributes:
        contract_name: Name of the contract that was processed.
        success: Whether CREATE TABLE succeeded (tags/grant are non-fatal).
        create_ddl: Generated CREATE TABLE DDL statement.
        tags_ddl: Generated ALTER TABLE SET TAGS statements.
        error: Error message if the operation failed (CREATE TABLE only).
        warnings: Non-fatal issues (e.g. tags skipped due to permissions).

    Example:
        >>> # Fully successful
        >>> result = RunResult(
        ...     contract_name="orders",
        ...     success=True,
        ...     create_ddl="CREATE TABLE...",
        ...     tags_ddl="ALTER TABLE SET TAGS...",
        ... )
        >>>
        >>> # Success with warnings (tag permission denied)
        >>> result = RunResult(
        ...     contract_name="orders",
        ...     success=True,
        ...     create_ddl="CREATE TABLE...",
        ...     warnings=["table (classification=Class_1): PERMISSION_DENIED: ..."],
        ... )
        >>>
        >>> # Failed (CREATE TABLE error)
        >>> result = RunResult(
        ...     contract_name="orders",
        ...     success=False,
        ...     error="AnalysisException: Table already exists",
        ... )
    """

    model_config = {"frozen": True}

    contract_name: str = Field(
        ...,
        description="Name of the contract processed",
        examples=["orders_v1", "customers_daily"],
    )
    success: bool = Field(
        ...,
        description="Whether the operation succeeded",
    )
    create_ddl: str = Field(
        default="",
        description="Generated CREATE TABLE DDL",
    )
    tags_ddl: str = Field(
        default="",
        description="Generated SET TAGS DDL statements",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if operation failed",
        examples=["Contract not found", "Invalid column type"],
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings (e.g. tags that could not be applied)",
    )

    @property
    def statements_count(self) -> int:
        """
        Count total DDL statements generated.

        Returns:
            Number of DDL statements (1 CREATE + N tags).

        Example:
            >>> result.statements_count
            3  # 1 CREATE + 2 TAG statements
        """
        tags_count = len([s for s in self.tags_ddl.split(";") if s.strip()])
        return 1 + tags_count
