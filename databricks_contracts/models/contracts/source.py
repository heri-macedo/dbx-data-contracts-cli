"""
Source model for data lineage information.

Defines the origin of data for lineage tracking and traceability.

Example:
    >>> from databricks_contracts.models.contracts import Source
    >>>
    >>> source = Source(
    ...     purview_fqn="mssql://server/database/schema/table",
    ...     type="SQL Server",
    ...     name="SourceSystem",
    ...     database="MainDB",
    ... )
"""

from typing import Optional

from pydantic import BaseModel, Field


class Source(BaseModel):
    """
    Data source information for lineage tracking.

    This is an optional section used for documenting data origins
    and enabling lineage traceability.

    Attributes:
        purview_fqn: Microsoft Purview fully qualified name.
        type: Source system type (e.g., "SQL Server", "Oracle").
        name: Source system name.
        database: Source database name.

    Example:
        >>> source = Source(
        ...     purview_fqn="mssql://prod-server/finance/dbo/transactions",
        ...     type="SQL Server",
        ...     name="FinanceDB",
        ...     database="finance",
        ... )
    """

    model_config = {"frozen": True, "extra": "forbid"}

    purview_fqn: Optional[str] = Field(
        default=None,
        description="Microsoft Purview fully qualified name",
        examples=["mssql://server/database/schema/table"],
    )
    type: Optional[str] = Field(
        default=None,
        description="Source system type",
        examples=["SQL Server", "Oracle", "PostgreSQL", "API"],
    )
    name: Optional[str] = Field(
        default=None,
        description="Source system name",
        examples=["FinanceDB", "CRMSystem"],
    )
    database: Optional[str] = Field(
        default=None,
        description="Source database name",
        examples=["finance", "sales"],
    )
