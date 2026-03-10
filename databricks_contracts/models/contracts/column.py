"""
Column model for table column definitions.

Represents a single column in a Unity Catalog table with its metadata,
type information, and optional privacy tags.

Example:
    >>> from databricks_contracts.models.contracts import Column, ColumnTags
    >>> from databricks_contracts.models.contracts.enums import Privacy
    >>>
    >>> column = Column(
    ...     name="customer_id",
    ...     type="STRING",
    ...     description="Unique customer identifier",
    ...     nullable=False,
    ...     tags=ColumnTags(privacy=Privacy.PII_A),
    ... )
"""

from typing import Optional

from pydantic import BaseModel, Field

from databricks_contracts.models.contracts.enums import Privacy


class ColumnTags(BaseModel):
    """
    Tags applied to a column in Unity Catalog.

    Attributes:
        privacy: Privacy classification for PII data.

    Example:
        >>> tags = ColumnTags(privacy=Privacy.PII_A)
        >>> print(tags.to_dict())  # {"privacy": "PII_A"}
    """

    model_config = {"frozen": True, "extra": "forbid"}

    privacy: Optional[Privacy] = Field(
        default=None,
        description="Privacy classification for PII data",
    )

    def to_dict(self) -> dict[str, str]:
        """
        Convert tags to dictionary, excluding None values.

        Returns:
            Dictionary with tag names and values.

        Example:
            >>> tags = ColumnTags(privacy=Privacy.PII_A)
            >>> tags.to_dict()
            {"privacy": "PII_A"}
        """
        result: dict[str, str] = {}
        if self.privacy:
            result["privacy"] = self.privacy.value
        return result


class Column(BaseModel):
    """
    Column definition within a table.

    Represents a single column with its type, description, and metadata.

    Attributes:
        name: Column name (must be valid SQL identifier).
        type: Databricks SQL type (STRING, INT, TIMESTAMP, etc.).
        description: Human-readable description of the column.
        nullable: Whether column accepts NULL values.
        tags: Optional column-level Unity Catalog tags.

    Example:
        >>> column = Column(
        ...     name="email",
        ...     type="STRING",
        ...     description="Customer email address",
        ...     nullable=True,
        ...     tags=ColumnTags(privacy=Privacy.PII_A),
        ... )
    """

    model_config = {"frozen": True, "extra": "forbid"}

    name: str = Field(
        ...,
        description="Column name (valid SQL identifier)",
        examples=["customer_id", "created_at"],
    )
    type: str = Field(
        ...,
        description="Databricks SQL type",
        examples=["STRING", "INT", "TIMESTAMP", "DECIMAL(18,2)"],
    )
    description: str = Field(
        ...,
        description="Human-readable column description",
        examples=["Unique customer identifier"],
    )
    nullable: bool = Field(
        default=True,
        description="Whether column accepts NULL values",
    )
    tags: Optional[ColumnTags] = Field(
        default=None,
        description="Column-level Unity Catalog tags",
    )
