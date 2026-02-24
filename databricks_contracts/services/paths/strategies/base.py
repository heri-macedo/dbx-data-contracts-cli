"""
Base path strategy interface.

Defines the contract for path resolution strategies.

Example:
    >>> from databricks_contracts.services.paths.strategies import PathStrategy
    >>>
    >>> class MyStrategy(PathStrategy):
    ...     def get_contracts_path(self):
    ...         return Path("/custom/path")
    ...     def get_config_path(self):
    ...         return Path("/custom/config.yaml")
"""

from abc import ABC, abstractmethod
from pathlib import Path


class PathStrategy(ABC):
    """
    Interface for path resolution strategies.

    Defines how to resolve paths for contracts and config files.
    Implementations provide environment-specific logic.

    Example:
        >>> class S3PathStrategy(PathStrategy):
        ...     def get_contracts_path(self) -> Path:
        ...         return Path("/dbfs/mnt/data/contracts")
        ...
        ...     def get_config_path(self) -> Path:
        ...         return Path("/dbfs/mnt/data/config.yaml")
    """

    @abstractmethod
    def get_contracts_path(self) -> Path:
        """
        Get path to contracts directory.

        Returns:
            Path to the contracts directory.

        Example:
            >>> strategy.get_contracts_path()
            Path("/project/contracts")
        """
        pass

    @abstractmethod
    def get_config_path(self) -> Path:
        """
        Get path to project configuration file.

        Returns:
            Path to datacontract.config.yaml.

        Example:
            >>> strategy.get_config_path()
            Path("/project/datacontract.config.yaml")
        """
        pass
