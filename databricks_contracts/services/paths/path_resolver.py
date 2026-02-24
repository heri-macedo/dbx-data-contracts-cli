"""
Path resolver service.

Resolves paths based on the current environment (local or Databricks).

Example:
    >>> from databricks_contracts.services.paths import PathResolverService
    >>> resolver = PathResolverService.create()
    >>> print(resolver.contracts_path)
"""

import os
from pathlib import Path
from typing import Optional

from databricks_contracts.config.constants import EnvironmentVariables
from databricks_contracts.services.paths.strategies.base import PathStrategy
from databricks_contracts.services.paths.strategies.databricks import DatabricksPathStrategy
from databricks_contracts.services.paths.strategies.local import LocalPathStrategy


class PathResolverService:
    """
    Service for resolving paths based on environment.

    Automatically detects whether running in Databricks or locally
    and uses the appropriate path resolution strategy.

    Attributes:
        strategy: Path resolution strategy in use.

    Example:
        >>> # Auto-detect environment
        >>> resolver = PathResolverService.create()
        >>>
        >>> # Get paths
        >>> print(resolver.contracts_path)
        Path("/project/contracts")
        >>> print(resolver.config_path)
        Path("/project/datacontract.config.yaml")
        >>>
        >>> # Force specific strategy
        >>> resolver = PathResolverService(strategy=LocalPathStrategy())
    """

    def __init__(self, strategy: Optional[PathStrategy] = None) -> None:
        """
        Initialize the path resolver.

        Args:
            strategy: Path strategy to use. If None, auto-detects.

        Example:
            >>> resolver = PathResolverService()  # Auto-detect
            >>> resolver = PathResolverService(strategy=LocalPathStrategy())
        """
        self._strategy = strategy or self._detect_strategy()

    @classmethod
    def create(cls) -> "PathResolverService":
        """
        Create resolver with auto-detected strategy.

        Returns:
            PathResolverService with appropriate strategy.

        Example:
            >>> resolver = PathResolverService.create()
        """
        return cls(strategy=None)

    def _detect_strategy(self) -> PathStrategy:
        """
        Detect environment and return appropriate strategy.

        Returns:
            DatabricksPathStrategy if in Databricks, else LocalPathStrategy.
        """
        if self._is_databricks():
            return DatabricksPathStrategy()
        return LocalPathStrategy()

    def _is_databricks(self) -> bool:
        """
        Check if running in Databricks runtime.

        Returns:
            True if DATABRICKS_RUNTIME_VERSION is set.
        """
        return os.environ.get(EnvironmentVariables.DATABRICKS_RUNTIME_VERSION) is not None

    @property
    def contracts_path(self) -> Path:
        """
        Get path to contracts directory.

        Returns:
            Path to contracts directory.

        Example:
            >>> resolver.contracts_path
            Path("/project/data_contracts/assets")
        """
        return self._strategy.get_contracts_path()

    @property
    def config_path(self) -> Path:
        """
        Get path to project configuration file.

        Returns:
            Path to datacontract.config.yaml.

        Example:
            >>> resolver.config_path
            Path("/project/datacontract.config.yaml")
        """
        return self._strategy.get_config_path()
