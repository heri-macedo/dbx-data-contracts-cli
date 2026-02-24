"""
Path strategies module.

Provides different strategies for path resolution:
- LocalPathStrategy: For local development
- DatabricksPathStrategy: For Databricks environment

Example:
    >>> from databricks_contracts.services.paths.strategies import LocalPathStrategy
    >>> strategy = LocalPathStrategy()
    >>> print(strategy.get_contracts_path())
"""

from databricks_contracts.services.paths.strategies.base import PathStrategy
from databricks_contracts.services.paths.strategies.databricks import DatabricksPathStrategy
from databricks_contracts.services.paths.strategies.local import LocalPathStrategy

__all__ = ["PathStrategy", "LocalPathStrategy", "DatabricksPathStrategy"]
