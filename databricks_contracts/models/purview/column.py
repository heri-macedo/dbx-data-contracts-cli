"""
Purview column models for Databricks Unity Catalog.

Represents databricks_table_column entities in Azure Purview catalog.

Example:
    >>> from databricks_contracts.models.purview import PurviewColumnEntity, PurviewColumnAttributes
    >>> attributes = PurviewColumnAttributes(
    ...     qualifiedName="databricks://metastore/catalog/schema/table#column_name",
    ...     name="column_name",
    ...     dataType="STRING",
    ...     comment="Column description",
    ... )
    >>> column = PurviewColumnEntity(attributes=attributes)
"""

from pydantic import BaseModel, Field

from databricks_contracts.models.purview.classification import PurviewClassification


class PurviewColumnAttributes(BaseModel):
    """
    Attributes for a databricks_table_column entity in Purview.

    Maps to the Databricks UC scan column type attributes.

    Attributes:
        qualifiedName: Unique identifier for the column in Purview.
        name: Column name.
        dataType: Column data type (STRING, INT, etc.).
        isNullable: Whether the column allows null values.
        ordinalPosition: Column position in the table.
        comment: Human-readable column description.

    Note:
        For privacy/PII tagging, use classifications on PurviewColumnEntity
        instead of tags (Purview API ignores tags for columns).

    Example:
        >>> attributes = PurviewColumnAttributes(
        ...     qualifiedName="databricks://metastore/catalog/schema/table#customer_id",
        ...     name="customer_id",
        ...     dataType="STRING",
        ...     isNullable=False,
        ...     ordinalPosition=1,
        ...     comment="Unique customer identifier",
        ... )
    """

    model_config = {"frozen": True}

    qualifiedName: str = Field(
        ...,
        description="Unique identifier for the column (table_qualified_name#column_name)",
        examples=["databricks://metastore/catalog/schema/table#customer_id"],
    )
    name: str = Field(
        ...,
        description="Column name",
        examples=["customer_id", "created_at", "email"],
    )
    dataType: str = Field(
        ...,
        description="Column data type",
        examples=["STRING", "INT", "TIMESTAMP", "DECIMAL(18,2)"],
    )
    isNullable: bool | None = Field(
        default=True,
        description="Whether the column allows null values",
    )
    ordinalPosition: int | None = Field(
        default=None,
        description="Column position in the table (0-based)",
        examples=[0, 1, 2],
    )
    comment: str | None = Field(
        default=None,
        description="Human-readable column description",
        examples=["Unique customer identifier"],
    )
    # Use classifications instead for privacy/PII tagging.


class PurviewColumnEntity(BaseModel):
    """
    Represents a databricks_table_column entity in Purview.

    Columns are related entities within a table entity and can have
    their own classifications (e.g., PII tags).

    Attributes:
        typeName: Entity type (databricks_table_column).
        attributes: Column metadata attributes.
        classifications: List of classifications applied to this column.

    Example:
        >>> column = PurviewColumnEntity(
        ...     attributes=PurviewColumnAttributes(...),
        ...     classifications=[PurviewClassification(typeName="PII_HIDDEN")],
        ... )
    """

    model_config = {"frozen": True}

    typeName: str = Field(
        default="databricks_table_column",
        description="Purview entity type for Databricks columns",
    )
    attributes: PurviewColumnAttributes = Field(
        ...,
        description="Column metadata attributes",
    )
    classifications: list[PurviewClassification] = Field(
        default_factory=list,
        description="Classifications applied to this column",
    )
