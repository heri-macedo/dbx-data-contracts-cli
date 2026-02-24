"""
Databricks Data Contracts - Apply data contracts to Unity Catalog.

A CLI tool for managing data contracts in Databricks Unity Catalog.
Supports contract validation, DDL generation, and job triggering.

Quick Start:
    $ pip install databricks-contracts
    $ databricks-contracts apply contract orders_v1
    $ databricks-contracts validate all

Modules:
    - models: Pydantic models for contracts, inputs, and results
    - adapters: External system integrations (Databricks, Git)
    - services: Business logic layer
    - handlers: Orchestration layer
    - commands: CLI interface
    - config: Configuration management

Example (Programmatic):
    >>> from databricks_contracts.handlers import ApplyHandler
    >>> from databricks_contracts.models.inputs import ApplyInput
    >>>
    >>> handler = ApplyHandler.create(environment="prod")
    >>> result = handler.handle(ApplyInput(contract_name="orders"))
    >>> print(result.success)
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("databricks-contracts")
except PackageNotFoundError:
    __version__ = "0.0.0"

__author__ = "Databricks PS LATAM Team"

# Core models
# Config
from databricks_contracts.config import get_logger, get_settings

# Handlers
from databricks_contracts.handlers import (
    ApplyHandler,
    TriggerHandler,
    ValidateHandler,
)
from databricks_contracts.models import (
    Column,
    Contract,
    Ownership,
    RunResult,
    Table,
    TriggerResult,
    ValidationResult,
)

__all__ = [
    # Version
    "__version__",
    # Models
    "Contract",
    "Column",
    "Table",
    "Ownership",
    "RunResult",
    "TriggerResult",
    "ValidationResult",
    # Handlers
    "ApplyHandler",
    "ValidateHandler",
    "TriggerHandler",
    # Config
    "get_settings",
    "get_logger",
]
