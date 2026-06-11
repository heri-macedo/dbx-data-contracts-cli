"""
Contract domain models.

Immutable Pydantic models representing the data contract structure.

Example:
    >>> from databricks_contracts.models.contracts import Contract, Table, Column
    >>> contract = Contract.model_validate(yaml_data)
    >>> print(contract.table.name)
"""

from databricks_contracts.models.contracts.column import Column, ColumnConstraints, ColumnTags
from databricks_contracts.models.contracts.contract import Contract, ContractInfo
from databricks_contracts.models.contracts.enums import (
    Classification,
    ContractStatus,
    Layer,
    Portfolio,
    Privacy,
    RefreshFrequency,
    SubDomain,
)
from databricks_contracts.models.contracts.ownership import Ownership
from databricks_contracts.models.contracts.source import Source
from databricks_contracts.models.contracts.table import Table, TableTags

__all__ = [
    "Contract",
    "ContractInfo",
    "Table",
    "TableTags",
    "Column",
    "ColumnConstraints",
    "ColumnTags",
    "Ownership",
    "Source",
    "ContractStatus",
    "RefreshFrequency",
    "Layer",
    "Classification",
    "Portfolio",
    "SubDomain",
    "Privacy",
]
