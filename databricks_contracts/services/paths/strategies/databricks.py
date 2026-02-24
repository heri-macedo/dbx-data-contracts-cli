"""
Databricks path strategy.

Resolves paths for Databricks runtime environment.

Example:
    >>> from databricks_contracts.services.paths.strategies import DatabricksPathStrategy
    >>> strategy = DatabricksPathStrategy()
    >>> print(strategy.get_contracts_path())
"""

import os
from functools import lru_cache
from pathlib import Path

from databricks_contracts.config.constants import EnvironmentVariables, FileNames
from databricks_contracts.config.settings import get_settings
from databricks_contracts.services.paths.strategies.base import PathStrategy

MAX_PARENT_LEVELS = 5


@lru_cache(maxsize=1)
def _find_path_upward(relative_path: str) -> Path:
    """
    Find path by searching from cwd upward.

    Handles cases where script runs from subdirectory but
    target is in project root.

    Args:
        relative_path: Relative path to search for.

    Returns:
        Found path or fallback to cwd-relative.
    """
    current = Path.cwd()

    for _ in range(MAX_PARENT_LEVELS):
        candidate = current / relative_path
        if candidate.exists():
            return candidate
        if current.parent == current:
            break
        current = current.parent

    return Path.cwd() / relative_path


class DatabricksPathStrategy(PathStrategy):
    """
    Path strategy for Databricks runtime environment.

    Handles path resolution when running in Databricks.
    Uses PROJECT_ROOT env var if set, otherwise searches upward.

    Example:
        >>> strategy = DatabricksPathStrategy()
        >>> print(strategy.get_contracts_path())
    """

    def __init__(self) -> None:
        """Initialize Databricks path strategy."""
        self._settings = get_settings()

    def get_contracts_path(self) -> Path:
        """
        Get path to contracts directory.

        Resolution order:
        1. PROJECT_ROOT env var + relative path
        2. Search upward from cwd

        Returns:
            Path to contracts directory.

        Example:
            >>> strategy.get_contracts_path()
            Path("/Workspace/project/data_contracts/assets")
        """
        return self._resolve_path(self._settings.CONTRACTS_PATH)

    def get_config_path(self) -> Path:
        """
        Get path to project configuration file.

        Returns:
            Path to datacontract.config.yaml.

        Example:
            >>> strategy.get_config_path()
            Path("/Workspace/project/datacontract.config.yaml")
        """
        return self._resolve_path(FileNames.PROJECT_CONFIG)

    def _resolve_path(self, relative_path: str) -> Path:
        """
        Resolve a relative path in Databricks environment.

        Args:
            relative_path: Relative path to resolve.

        Returns:
            Resolved absolute path.
        """
        # Priority 1: Explicit PROJECT_ROOT env var
        project_root = os.environ.get(EnvironmentVariables.PROJECT_ROOT)
        if project_root:
            return Path(project_root) / relative_path

        # Priority 2: Search upward from cwd
        return _find_path_upward(relative_path)
