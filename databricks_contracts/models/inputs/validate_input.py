"""
Validate input model for ValidateHandler.

Validates input for contract validation operations.

Example:
    >>> from databricks_contracts.models.inputs import ValidateInput
    >>> input = ValidateInput(contract_name="my_contract")
    >>> input = ValidateInput()  # Validate all contracts
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ValidateInput(BaseModel):
    """
    Input DTO for ValidateHandler.

    Validates the input parameters for contract validation operations.

    Attributes:
        contract_name: Name of contract to validate, or None for all contracts.

    Example:
        >>> # Validate single contract
        >>> input = ValidateInput(contract_name="orders_v1")
        >>>
        >>> # Validate all contracts
        >>> input = ValidateInput()

    Raises:
        ValidationError: If contract_name is provided but empty.
    """

    model_config = {"frozen": True}

    contract_name: Optional[str] = Field(
        default=None,
        description="Contract name to validate, or None for all",
        examples=["customer_orders_v1", None],
    )

    @field_validator("contract_name")
    @classmethod
    def clean_contract_name(cls, v: Optional[str]) -> Optional[str]:
        """
        Remove .yaml extension if present and strip whitespace.

        Args:
            v: Raw contract name from input or None.

        Returns:
            Cleaned contract name or None.

        Example:
            >>> ValidateInput(contract_name="test.yaml").contract_name
            "test"
        """
        if v is None:
            return None
        cleaned = v.removesuffix(".yaml").strip()
        return cleaned if cleaned else None

    @property
    def validate_all(self) -> bool:
        """
        Check if should validate all contracts.

        Returns:
            True if no specific contract is specified.

        Example:
            >>> ValidateInput().validate_all
            True
            >>> ValidateInput(contract_name="test").validate_all
            False
        """
        return self.contract_name is None
