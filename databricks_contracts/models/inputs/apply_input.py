"""
Apply input model for ApplyHandler.

Validates and normalizes input for contract application operations.

Example:
    >>> from databricks_contracts.models.inputs import ApplyInput
    >>> input = ApplyInput(contract_name="my_contract.yaml", environment="prod")
    >>> print(input.contract_name)  # "my_contract" (extension removed)
"""

from pydantic import BaseModel, Field, field_validator


class ApplyInput(BaseModel):
    """
    Input DTO for ApplyHandler.

    Validates and normalizes the input parameters for applying a contract
    to Unity Catalog.

    Attributes:
        contract_name: Name of the contract (without .yaml extension).
        environment: Target environment (dev or prod).

    Example:
        >>> input = ApplyInput(contract_name="orders_v1", environment="dev")
        >>> input = ApplyInput(contract_name="orders_v1.yaml")  # .yaml is stripped

    Raises:
        ValidationError: If contract_name is empty or environment is invalid.
    """

    model_config = {"frozen": True}

    contract_name: str = Field(
        ...,
        min_length=1,
        description="Contract name (without .yaml extension)",
        examples=["customer_orders_v1", "transactions_daily"],
    )
    environment: str = Field(
        default="dev",
        pattern=r"^(dev|prod)$",
        description="Target environment (dev or prod)",
        examples=["dev", "prod"],
    )

    @field_validator("contract_name")
    @classmethod
    def clean_contract_name(cls, v: str) -> str:
        """
        Remove .yaml extension if present and strip whitespace.

        Args:
            v: Raw contract name from input.

        Returns:
            Cleaned contract name without extension.

        Example:
            >>> ApplyInput(contract_name="test.yaml").contract_name
            "test"
        """
        return v.removesuffix(".yaml").strip()
