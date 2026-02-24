"""
Validation result model for contract validation operations.

Represents the result of validating a contract YAML file.

Example:
    >>> from databricks_contracts.models.results import ValidationResult
    >>> result = ValidationResult(contract_name="orders", valid=True)
"""

from typing import Optional

from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """
    Result of validating a contract.

    Immutable model containing the outcome of contract validation.

    Attributes:
        contract_name: Name of the contract validated.
        valid: Whether the contract is valid.
        error: Error message if validation failed.
        error_count: Number of validation errors.

    Example:
        >>> # Valid contract
        >>> result = ValidationResult(contract_name="orders", valid=True)
        >>>
        >>> # Invalid contract
        >>> result = ValidationResult(
        ...     contract_name="orders",
        ...     valid=False,
        ...     error="Missing required field: description",
        ...     error_count=1,
        ... )
    """

    model_config = {"frozen": True}

    contract_name: str = Field(
        ...,
        description="Name of the contract validated",
        examples=["orders_v1"],
    )
    valid: bool = Field(
        ...,
        description="Whether the contract is valid",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if validation failed",
    )
    error_count: int = Field(
        default=0,
        ge=0,
        description="Number of validation errors",
    )
