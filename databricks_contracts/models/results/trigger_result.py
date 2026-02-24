"""
Trigger result model for job trigger operations.

Represents the result of triggering a Databricks job.

Example:
    >>> from databricks_contracts.models.results import TriggerResult
    >>> result = TriggerResult(
    ...     contract_name="orders",
    ...     success=True,
    ...     run_id=12345,
    ...     run_url="https://...",
    ... )
"""

from typing import Optional

from pydantic import BaseModel, Field


class TriggerResult(BaseModel):
    """
    Result of triggering a Databricks job.

    Immutable model containing the outcome of a job trigger operation.

    Attributes:
        contract_name: Name of the contract the job was triggered for.
        success: Whether the trigger succeeded.
        run_id: Databricks run ID if successful.
        run_url: URL to the job run in Databricks UI.
        error: Error message if trigger failed.

    Example:
        >>> # Successful trigger
        >>> result = TriggerResult(
        ...     contract_name="orders",
        ...     success=True,
        ...     run_id=123456,
        ...     run_url="https://workspace.databricks.com/#job/1/run/123456",
        ... )
        >>>
        >>> # Failed trigger
        >>> result = TriggerResult(
        ...     contract_name="orders",
        ...     success=False,
        ...     error="Job not found: Apply Contract - orders",
        ... )
    """

    model_config = {"frozen": True}

    contract_name: str = Field(
        ...,
        description="Name of the contract",
        examples=["orders_v1"],
    )
    success: bool = Field(
        ...,
        description="Whether the trigger succeeded",
    )
    run_id: Optional[int] = Field(
        default=None,
        description="Databricks run ID",
        examples=[123456],
    )
    run_url: Optional[str] = Field(
        default=None,
        description="URL to the run in Databricks UI",
        examples=["https://workspace.databricks.com/#job/1/run/123456"],
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if trigger failed",
        examples=["Job not found", "API timeout"],
    )
