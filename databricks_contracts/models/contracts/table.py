"""
Table model for Unity Catalog table definitions.

Represents a complete table definition including columns, tags, and metadata.

Example:
    >>> from databricks_contracts.models.contracts import Table, TableTags, Column
    >>> from databricks_contracts.models.contracts.enums import Layer, RefreshFrequency
    >>>
    >>> table = Table(
    ...     name="customers",
    ...     description="Customer master data",
    ...     refresh_frequency=RefreshFrequency.DAILY,
    ...     retention_days=365,
    ...     tags=TableTags(layer=Layer.LAYER_3),
    ...     columns=[
    ...         Column(name="id", type="STRING", description="ID"),
    ...     ],
    ... )
"""

from typing import Optional

from pydantic import BaseModel, Field, model_validator

from databricks_contracts.models.contracts.column import Column
from databricks_contracts.models.contracts.enums import Classification, Layer, RefreshFrequency


class TableTags(BaseModel):
    """
    Tags applied to a table in Unity Catalog.

    Attributes:
        layer: Data layer classification (required).
        classification: Data classification (optional).
        data_exchange: Data exchange flag (optional).

    Example:
        >>> tags = TableTags(
        ...     layer=Layer.LAYER_3,
        ...     classification=Classification.CLASS_C,
        ... )
        >>> print(tags.to_dict())
        {"layer": "Layer_3", "classification": "Class_C"}
    """

    model_config = {"frozen": True, "extra": "forbid"}

    layer: Layer = Field(
        ...,
        description="Data layer classification (Layer_1, Layer_2, Layer_3)",
    )
    classification: Optional[Classification] = Field(
        default=None,
        description="Data classification for governance",
    )
    data_exchange: Optional[str] = Field(
        default=None,
        description="Data exchange flag",
    )

    def to_dict(self) -> dict[str, str]:
        """
        Convert tags to dictionary, excluding None values.

        Returns:
            Dictionary with tag names and values.

        Example:
            >>> tags = TableTags(layer=Layer.LAYER_3)
            >>> tags.to_dict()
            {"layer": "Layer_3"}
        """
        result: dict[str, str] = (
            {"layer": self.layer.layer} if hasattr(self.layer, "layer") else {"layer": self.layer.value}
        )
        # Wait, I should just use self.layer.value
        result = {"layer": self.layer.value}
        if self.classification:
            result["classification"] = self.classification.value
        if self.data_exchange:
            result["data_exchange"] = self.data_exchange
        return result


class Table(BaseModel):
    """
    Table definition within a data contract.

    Represents a complete Unity Catalog table with columns, tags, and metadata.

    Attributes:
        name: Table name (must be valid SQL identifier).
        description: Human-readable table description.
        refresh_frequency: How often the data is refreshed.
        retention_days: Data retention period in days.
        tags: Table-level Unity Catalog tags.
        columns: List of column definitions (at least one required).
        partitioned_by: Optional list of column names for Delta table partitioning.

    Example:
        >>> table = Table(
        ...     name="orders",
        ...     description="Customer orders",
        ...     refresh_frequency=RefreshFrequency.HOURLY,
        ...     retention_days=90,
        ...     tags=TableTags(layer=Layer.LAYER_2),
        ...     columns=[...],
        ...     partitioned_by=["order_date"],
        ... )
    """

    model_config = {"frozen": True, "extra": "forbid"}

    name: str = Field(
        ...,
        description="Table name (valid SQL identifier)",
        examples=["customers", "orders", "transactions"],
    )
    description: str = Field(
        ...,
        description="Human-readable table description",
        examples=["Customer master data table"],
    )
    refresh_frequency: RefreshFrequency = Field(
        ...,
        description="Data refresh frequency",
    )
    retention_days: int = Field(
        ...,
        ge=1,
        description="Data retention in days",
        examples=[30, 90, 365],
    )
    tags: TableTags = Field(
        ...,
        description="Table-level Unity Catalog tags",
    )
    columns: list[Column] = Field(
        ...,
        min_length=1,
        description="List of column definitions (at least one required)",
    )
    partitioned_by: Optional[list[str]] = Field(
        default=None,
        description="Column names for Delta table partitioning",
        examples=[["order_date"], ["year", "month"]],
    )

    @model_validator(mode="after")
    def validate_partition_columns(self) -> "Table":
        """
        Validate that partition columns exist in the table column definitions.

        Raises:
            ValueError: If any partition column is not defined in ``columns``.

        Example:
            >>> table = Table(
            ...     name="orders",
            ...     columns=[Column(name="id", type="STRING", description="ID")],
            ...     partitioned_by=["missing_col"],
            ... )  # raises ValueError
        """
        if self.partitioned_by:
            column_names = {col.name for col in self.columns}
            invalid = [col for col in self.partitioned_by if col not in column_names]
            if invalid:
                raise ValueError(f"Partition columns not found in table columns: {invalid}")
        return self
