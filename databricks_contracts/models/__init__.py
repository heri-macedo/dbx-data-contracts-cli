"""
Models module - All Pydantic models for the application.

This module provides:
- contracts/: Domain models (Contract, Table, Column, etc.)
- inputs/: Input DTOs for handlers (ApplyInput, ValidateInput, etc.)
- results/: Output DTOs from handlers (RunResult, TriggerResult, etc.)
- statements/: DDL statement models (CreateTableStatement, TagStatement, etc.)

Example:
    >>> from databricks_contracts.models import Contract, ApplyInput, RunResult
    >>> from databricks_contracts.models.contracts import Column, Table
"""

# Domain models
from databricks_contracts.models.contracts import (
    Column,
    ColumnTags,
    Contract,
    ContractInfo,
    Ownership,
    Source,
    Table,
    TableTags,
)
from databricks_contracts.models.contracts.enums import (
    Classification,
    ContractStatus,
    Layer,
    Portfolio,
    Privacy,
    RefreshFrequency,
    SubDomain,
)

# Input DTOs
from databricks_contracts.models.inputs import ApplyInput, TriggerInput, ValidateInput

# Result DTOs
from databricks_contracts.models.results import (
    ExecutionResult,
    RunResult,
    TriggerResult,
    ValidationResult,
)

# Statement models
from databricks_contracts.models.statements import (
    BaseStatement,
    CreateTableStatement,
    TagStatement,
)

__all__ = [
    # Domain models
    "Contract",
    "ContractInfo",
    "Table",
    "TableTags",
    "Column",
    "ColumnTags",
    "Ownership",
    "Source",
    # Enums
    "ContractStatus",
    "RefreshFrequency",
    "Layer",
    "Classification",
    "Portfolio",
    "SubDomain",
    "Privacy",
    # Inputs
    "ApplyInput",
    "ValidateInput",
    "TriggerInput",
    # Results
    "RunResult",
    "ValidationResult",
    "TriggerResult",
    "ExecutionResult",
    # Statements
    "BaseStatement",
    "CreateTableStatement",
    "TagStatement",
]
