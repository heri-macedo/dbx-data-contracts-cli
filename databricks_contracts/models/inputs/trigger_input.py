"""
Trigger input model for TriggerHandler.

Validates input for job trigger operations.

Example:
    >>> from databricks_contracts.models.inputs import TriggerInput
    >>> input = TriggerInput(contracts=["order_v1", "customer_v1"])
"""

from pydantic import BaseModel, Field, field_validator


class TriggerInput(BaseModel):
    """
    Input DTO for TriggerHandler.

    Validates the input parameters for triggering Databricks jobs.

    Attributes:
        contracts: List of contract names to trigger jobs for.
        base_ref: Git base reference for detecting modified contracts.

    Example:
        >>> # Trigger specific contracts
        >>> input = TriggerInput(contracts=["orders_v1", "customers_v1"])
        >>>
        >>> # With custom git ref
        >>> input = TriggerInput(
        ...     contracts=["orders_v1"],
        ...     base_ref="origin/main",
        ... )

    Raises:
        ValidationError: If contracts list is empty.
    """

    model_config = {"frozen": True}

    contracts: list[str] = Field(
        ...,
        min_length=1,
        description="List of contract names to trigger",
        examples=[["orders_v1", "customers_v1"]],
    )
    base_ref: str = Field(
        default="HEAD~1",
        description="Git base reference for diff (used in modified detection)",
        examples=["HEAD~1", "origin/main", "develop"],
    )

    @field_validator("contracts")
    @classmethod
    def clean_contract_names(cls, v: list[str]) -> list[str]:
        """
        Remove .yaml extensions and strip whitespace from all contracts.

        Args:
            v: Raw list of contract names.

        Returns:
            Cleaned list of contract names.

        Example:
            >>> TriggerInput(contracts=["a.yaml", "b"]).contracts
            ["a", "b"]
        """
        return [name.removesuffix(".yaml").strip() for name in v]
