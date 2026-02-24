"""
Contract model - Root model for data contracts.

This is the main entry point for loading and validating YAML contract files.

Example:
    >>> import yaml
    >>> from databricks_contracts.models.contracts import Contract
    >>>
    >>> with open("my_contract.yaml") as f:
    ...     data = yaml.safe_load(f)
    >>> contract = Contract.model_validate(data)
    >>> print(contract.full_table_name)
    "catalog.schema.table_name"
"""

from typing import Optional

from pydantic import BaseModel, Field

from databricks_contracts.models.contracts.enums import ContractStatus
from databricks_contracts.models.contracts.ownership import Ownership
from databricks_contracts.models.contracts.source import Source
from databricks_contracts.models.contracts.table import Table


class ContractInfo(BaseModel):
    """
    Contract metadata (name, version, status).

    Attributes:
        name: Unique contract identifier.
        version: Semantic version of the contract.
        status: Lifecycle status (draft, active, deprecated).

    Example:
        >>> info = ContractInfo(
        ...     name="customer_orders_v1",
        ...     version="1.0.0",
        ...     status=ContractStatus.ACTIVE,
        ... )
    """

    model_config = {"frozen": True}

    name: str = Field(
        ...,
        description="Unique contract identifier",
        examples=["customer_orders_v1", "transactions_daily"],
    )
    version: str = Field(
        ...,
        description="Semantic version of the contract",
        examples=["1.0.0", "2.1.0"],
    )
    status: ContractStatus = Field(
        default=ContractStatus.DRAFT,
        description="Lifecycle status of the contract",
    )


class Contract(BaseModel):
    """
    Root contract model representing a complete Data Contract.

    This is the main model for parsing and validating YAML contract files.
    It contains all information needed to create a Unity Catalog table
    with proper metadata, tags, and governance information.

    Attributes:
        contract: Contract metadata (name, version, status).
        catalog: Unity Catalog catalog name (from YAML, may be overridden).
        schema_name: Unity Catalog schema name (from YAML, may be overridden).
        ownership: Ownership and governance information.
        table: Table definition with columns and tags.
        source: Optional data source information for lineage.

    Example:
        >>> contract = Contract.model_validate(yaml_data)
        >>> print(contract.name)           # "my_contract"
        >>> print(contract.version)        # "1.0.0"
        >>> print(contract.full_table_name) # "catalog.schema.table"
    """

    model_config = {"frozen": True, "populate_by_name": True}

    contract: ContractInfo = Field(
        ...,
        description="Contract metadata (name, version, status)",
    )
    catalog: str = Field(
        ...,
        description="Unity Catalog catalog name",
        examples=["test_catalog", "analytics"],
    )
    schema_name: str = Field(
        ...,
        alias="schema",
        description="Unity Catalog schema name",
        examples=["test_schema", "finance"],
    )
    ownership: Ownership = Field(
        ...,
        description="Ownership and governance information",
    )
    table: Table = Field(
        ...,
        description="Table definition with columns and tags",
    )
    source: Optional[Source] = Field(
        default=None,
        description="Optional data source for lineage",
    )

    @property
    def full_table_name(self) -> str:
        """
        Get fully qualified table name.

        Returns:
            String in format "catalog.schema.table".

        Example:
            >>> contract.full_table_name
            "test_catalog.test_schema.test_table"
        """
        return f"{self.catalog}.{self.schema_name}.{self.table.name}"

    @property
    def name(self) -> str:
        """
        Shortcut to contract name.

        Returns:
            Contract name from metadata.

        Example:
            >>> contract.name
            "customer_orders_v1"
        """
        return self.contract.name

    @property
    def version(self) -> str:
        """
        Shortcut to contract version.

        Returns:
            Contract version from metadata.

        Example:
            >>> contract.version
            "1.0.0"
        """
        return self.contract.version
