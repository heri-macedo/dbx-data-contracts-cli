"""
Services module - Business logic layer.

This module provides services that orchestrate business logic:
- contracts/: Contract loading and DDL building
- git/: Change detection for contracts
- databricks/: Job triggering
- paths/: Path resolution for different environments
- purview/: Contract publishing to Microsoft Purview

Example:
    >>> from databricks_contracts.services import ContractLoaderService, BuilderService
    >>> loader = ContractLoaderService()
    >>> contract = loader.load("my_contract")
"""

from databricks_contracts.services.contracts import BuilderService, ContractLoaderService
from databricks_contracts.services.databricks import TriggerService
from databricks_contracts.services.git import ChangeDetectorService
from databricks_contracts.services.paths import PathResolverService
from databricks_contracts.services.purview import ContractToPurviewMapper, PurviewPublisherService

__all__ = [
    "ContractLoaderService",
    "BuilderService",
    "ChangeDetectorService",
    "TriggerService",
    "PathResolverService",
    "ContractToPurviewMapper",
    "PurviewPublisherService",
]
