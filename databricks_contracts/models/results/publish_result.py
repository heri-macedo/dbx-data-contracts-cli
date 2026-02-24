"""
Publish result model for contract publishing to Purview.

Represents the result of publishing a contract to Microsoft Purview.

Example:
    >>> from databricks_contracts.models.results import PublishResult
    >>> result = PublishResult(
    ...     contract_name="orders_v1",
    ...     success=True,
    ...     purview_collection_name="MyCollection",
    ... )
"""

from typing import Optional

from pydantic import BaseModel, Field


class PublishResult(BaseModel):
    """
    Result of publishing a contract to Microsoft Purview.

    Immutable model containing the outcome of a publish operation.

    Attributes:
        contract_name: Name of the contract that was processed.
        success: Whether the operation succeeded.
        purview_collection_name: Name of the Purview collection where entity was published.
        purview_qualified_name: Qualified name of the entity in Purview.
        error: Error message if the operation failed.

    Example:
        >>> # Successful result
        >>> result = PublishResult(
        ...     contract_name="orders",
        ...     success=True,
        ...     purview_collection_name="DataContracts",
        ...     purview_qualified_name="databricks://catalog.schema.orders",
        ... )
        >>>
        >>> # Failed result
        >>> result = PublishResult(
        ...     contract_name="orders",
        ...     success=False,
        ...     error="Authentication failed: Invalid token",
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
    purview_collection_name: Optional[str] = Field(
        default=None,
        description="Purview collection where entity was published",
        examples=["DataContracts", "Production"],
    )
    purview_qualified_name: Optional[str] = Field(
        default=None,
        description="Qualified name of the entity in Purview",
        examples=["databricks://catalog.schema.table"],
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if operation failed",
        examples=["Authentication failed", "Collection not found"],
    )
