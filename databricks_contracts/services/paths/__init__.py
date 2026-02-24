"""
Path services module.

Provides path resolution for different environments:
- PathResolverService: Resolve paths for local or Databricks

Example:
    >>> from databricks_contracts.services.paths import PathResolverService
    >>> resolver = PathResolverService.create()
    >>> print(resolver.contracts_path)
"""

from databricks_contracts.services.paths.path_resolver import PathResolverService
from databricks_contracts.services.paths.strategies import (
    DatabricksPathStrategy,
    LocalPathStrategy,
    PathStrategy,
)

__all__ = [
    "PathResolverService",
    "PathStrategy",
    "LocalPathStrategy",
    "DatabricksPathStrategy",
]
