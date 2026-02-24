"""
Purview adapters for Azure Purview API integration.

Provides client implementations for interacting with Microsoft Purview.

Example:
    >>> from databricks_contracts.adapters.purview import PurviewCatalogApiClient
    >>> client = PurviewCatalogApiClient.from_environment_variables()
    >>> client.create_or_update_entity(payload, collection_name="MyCollection")
"""

from databricks_contracts.adapters.purview.api_client import PurviewCatalogApiClient
from databricks_contracts.adapters.purview.base import BasePurviewClient
from databricks_contracts.adapters.purview.dry_run_client import DryRunPurviewClient

__all__ = [
    "BasePurviewClient",
    "PurviewCatalogApiClient",
    "DryRunPurviewClient",
]
