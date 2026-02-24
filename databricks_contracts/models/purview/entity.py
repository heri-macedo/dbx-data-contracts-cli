"""
Purview table entity model for Databricks Unity Catalog.

Represents a databricks_table entity in Azure Purview catalog.

API Documentation:
    - Entity Create/Update: https://learn.microsoft.com/en-us/rest/api/purview/datamapdataplane/entity/create-or-update
    - AtlasEntity Schema: https://learn.microsoft.com/en-us/rest/api/purview/datamapdataplane/entity/create-or-update#atlasentity

Example:
    >>> from databricks_contracts.models.purview import PurviewTableEntity, PurviewTableAttributes
    >>> attributes = PurviewTableAttributes(
    ...     qualifiedName="databricks://metastore/catalog/schema/table",
    ...     name="table",
    ...     catalogName="catalog",
    ...     schemaName="schema",
    ... )
    >>> entity = PurviewTableEntity(attributes=attributes)
    >>> payload = entity.to_json()
"""

from typing import Any

from pydantic import BaseModel, Field

from databricks_contracts.models.purview.classification import PurviewClassification
from databricks_contracts.models.purview.column import PurviewColumnEntity


class PurviewTableAttributes(BaseModel):
    """
    Attributes for a databricks_table entity in Purview.

    Maps to the Databricks UC scan type attributes.

    Attributes:
        qualifiedName: Unique identifier for the table in Purview.
        name: Table name.
        catalogName: Unity Catalog name.
        schemaName: Schema name.
        comment: Table description/comment.
        tags: Custom tags map (portfolio, sub_domain, layer, etc.).

    Example:
        >>> attributes = PurviewTableAttributes(
        ...     qualifiedName="databricks://metastore/catalog/schema/customers",
        ...     name="customers",
        ...     catalogName="catalog",
        ...     schemaName="schema",
        ...     comment="Customer master data",
        ...     tags={"portfolio": "Portfolio_1", "layer": "Gold"},
        ... )
    """

    model_config = {"frozen": True}

    qualifiedName: str = Field(
        ...,
        description="Unique identifier for the table in Purview",
        examples=["databricks://metastore/catalog/schema/table"],
    )
    name: str = Field(
        ...,
        description="Table name",
        examples=["customers", "orders", "transactions"],
    )
    catalogName: str = Field(
        ...,
        description="Unity Catalog name",
        examples=["my_catalog"],
    )
    schemaName: str = Field(
        ...,
        description="Schema name",
        examples=["my_schema"],
    )
    comment: str | None = Field(
        default=None,
        description="Table description/comment",
        examples=["Customer master data table"],
    )
    tableType: str | None = Field(
        default="MANAGED",
        description="Table type (MANAGED, EXTERNAL)",
        examples=["MANAGED", "EXTERNAL"],
    )
    tags: dict[str, str] | None = Field(
        default=None,
        description="Custom tags map (portfolio, sub_domain, layer, classification, etc.)",
        examples=[{"portfolio": "Portfolio_1", "layer": "Gold", "sub_domain": "Sub_Domain_1"}],
    )


class PurviewTableEntity(BaseModel):
    """
    Represents a databricks_table entity in Azure Purview.

    This is the main entity model for publishing Databricks tables to Purview.
    It includes table attributes, classifications, and related column entities.

    Attributes:
        typeName: Entity type (databricks_table).
        attributes: Table metadata attributes.
        classifications: List of classifications applied to the table.
        columns: Column entities for this table.

    Example:
        >>> entity = PurviewTableEntity(
        ...     attributes=PurviewTableAttributes(...),
        ...     classifications=[PurviewClassification(typeName="Classification_1")],
        ... )
        >>> payload = entity.to_json()
    """

    model_config = {"frozen": True}

    typeName: str = Field(
        default="databricks_table",
        description="Purview entity type for Databricks tables",
    )
    attributes: PurviewTableAttributes = Field(
        ...,
        description="Table metadata attributes",
    )
    classifications: list[PurviewClassification] = Field(
        default_factory=list,
        description="Classifications applied to the table",
    )
    columns: list[PurviewColumnEntity] = Field(
        default_factory=list,
        description="Column entities for this table",
    )

    def to_json(self, exclude_none: bool = True) -> dict[str, Any]:
        """
        Generate JSON payload with table and columns using negative GUIDs.

        Creates a payload with bidirectional relationships between table and columns
        using negative GUIDs (temporary IDs). This follows the official Purview/Atlas
        API format for creating related entities in a single bulk request.

        The table references columns via relationshipAttributes.columns, and each
        column references the table via relationshipAttributes.table.

        API Documentation:
            - Entity Create/Update:
              https://learn.microsoft.com/en-us/rest/api/purview/datamapdataplane/entity/create-or-update
            - Create assets and lineage relationships (negative GUIDs):
              https://learn.microsoft.com/en-us/purview/create-relationships

        Args:
            exclude_none: Whether to exclude None values from output.

        Returns:
            Dict with 'entities' array matching AtlasEntitiesWithExtInfo schema.

        Example:
            >>> entity = PurviewTableEntity(...)
            >>> payload = entity.to_json()
            >>> # {"entities": [table_entity, column1_entity, column2_entity, ...]}
        """
        # Negative GUID for table (temporary ID for bulk creation)
        table_guid = "-1"

        # Table entity (without columns field - they become separate entities)
        table_data = self.model_dump(by_alias=True, exclude_none=exclude_none, exclude={"columns"})
        table_data["guid"] = table_guid

        entities = []

        # Build column entities with negative GUIDs and bidirectional relationships
        column_refs = []
        for idx, column in enumerate(self.columns):
            column_guid = f"-{idx + 2}"  # -2, -3, -4, ...

            column_data = column.model_dump(by_alias=True, exclude_none=exclude_none)
            column_data["guid"] = column_guid
            # Column references table via relationshipAttributes.table
            column_data["relationshipAttributes"] = {
                "table": {
                    "guid": table_guid,
                    "typeName": self.typeName,
                }
            }
            entities.append(column_data)

            # Reference for table's relationshipAttributes.columns
            column_refs.append(
                {
                    "guid": column_guid,
                    "typeName": column.typeName,
                }
            )

        # Add relationshipAttributes.columns to table entity (bidirectional)
        if column_refs:
            table_data["relationshipAttributes"] = {"columns": column_refs}

        # Table first, then columns
        return {"entities": [table_data] + entities}
