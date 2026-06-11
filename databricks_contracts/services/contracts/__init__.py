"""
Contract services module.

Provides business logic for contract operations:
- ContractLoaderService: Load and validate contracts
- BuilderService: Build DDL statements

Example:
    >>> from databricks_contracts.services.contracts import ContractLoaderService
    >>> loader = ContractLoaderService()
    >>> contract = loader.load("my_contract")
"""

from databricks_contracts.services.contracts.builder import BuilderService
from databricks_contracts.services.contracts.loader import ContractLoaderService
from databricks_contracts.services.contracts.schema_differ import SchemaDifferService

__all__ = ["ContractLoaderService", "BuilderService", "SchemaDifferService"]
