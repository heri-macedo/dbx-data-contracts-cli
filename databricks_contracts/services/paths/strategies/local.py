"""
Local path strategy for development.

Resolves paths for local development environment.

Example:
    >>> from databricks_contracts.services.paths.strategies import LocalPathStrategy
    >>> strategy = LocalPathStrategy()
    >>> print(strategy.get_contracts_path())
    Path("data_contracts/assets")
"""

from pathlib import Path
from typing import Optional

from databricks_contracts.config.constants import FileNames
from databricks_contracts.config.settings import get_settings
from databricks_contracts.services.paths.strategies.base import PathStrategy


class LocalPathStrategy(PathStrategy):
    """
    Path strategy for local development.

    Uses paths relative to current directory or explicit base path.

    Attributes:
        base_path: Base directory for path resolution.

    Example:
        >>> strategy = LocalPathStrategy()
        >>> print(strategy.get_contracts_path())
        Path("data_contracts/assets")
        >>>
        >>> strategy = LocalPathStrategy(base_path=Path("/project"))
        >>> print(strategy.get_contracts_path())
        Path("/project/data_contracts/assets")
    """

    def __init__(self, base_path: Optional[Path] = None) -> None:
        """
        Initialize local path strategy.

        Args:
            base_path: Base directory. Defaults to current directory.

        Example:
            >>> strategy = LocalPathStrategy()  # Uses cwd
            >>> strategy = LocalPathStrategy(Path("/project"))  # Explicit
        """
        self._base = base_path or Path.cwd()
        self._settings = get_settings()

    def get_contracts_path(self) -> Path:
        """
        Get path to contracts directory.

        Uses CONTRACTS_PATH from settings or default.

        Returns:
            Path to contracts directory.

        Example:
            >>> strategy.get_contracts_path()
            Path("/project/data_contracts/assets")
        """
        return self._base / self._settings.CONTRACTS_PATH

    def get_config_path(self) -> Path:
        """
        Get path to project configuration file.

        Returns:
            Path to datacontract.config.yaml.

        Example:
            >>> strategy.get_config_path()
            Path("/project/datacontract.config.yaml")
        """
        return self._base / FileNames.PROJECT_CONFIG
