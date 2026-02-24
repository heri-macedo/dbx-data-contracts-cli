"""
Change detector service.

Detects modified contracts using Git.

Example:
    >>> from databricks_contracts.services.git import ChangeDetectorService
    >>> detector = ChangeDetectorService.create()
    >>> contracts = detector.get_modified_contracts()
    >>> print(contracts)
    ["orders_v1", "customers_v1"]
"""

from pathlib import Path

from databricks_contracts.adapters.git.base import ChangeDetectorPort
from databricks_contracts.adapters.git.subprocess_adapter import SubprocessGitAdapter
from databricks_contracts.services.paths import PathResolverService


class ChangeDetectorService:
    """
    Service for detecting modified contracts via Git.

    Uses a Git adapter to find modified files, then filters
    to only include contract YAML files.

    Attributes:
        git_adapter: Git adapter for change detection.
        contracts_path: Path to contracts directory.

    Example:
        >>> # Create with default settings
        >>> detector = ChangeDetectorService.create()
        >>>
        >>> # Get modified contracts
        >>> contracts = detector.get_modified_contracts()
        >>> print(contracts)
        ["orders_v1", "customers_v1"]
        >>>
        >>> # With custom base ref
        >>> contracts = detector.get_modified_contracts(base_ref="origin/main")
    """

    FILE_EXTENSION = ".yaml"

    def __init__(
        self,
        git_adapter: ChangeDetectorPort,
        contracts_path: Path,
    ) -> None:
        """
        Initialize the change detector service.

        Args:
            git_adapter: Git adapter for detecting changes.
            contracts_path: Path to contracts directory.

        Example:
            >>> adapter = SubprocessGitAdapter()
            >>> detector = ChangeDetectorService(adapter, Path("./contracts"))
        """
        self._git = git_adapter
        self._contracts_path = str(contracts_path.resolve())

    @classmethod
    def create(cls) -> "ChangeDetectorService":
        """
        Create service with default dependencies.

        Returns:
            ChangeDetectorService with subprocess adapter and auto-resolved path.

        Example:
            >>> detector = ChangeDetectorService.create()
        """
        git_adapter = SubprocessGitAdapter()
        contracts_path = PathResolverService.create().contracts_path
        return cls(git_adapter, contracts_path)

    def get_modified_contracts(
        self,
        base_ref: str = "HEAD~1",
        head_ref: str = "HEAD",
    ) -> list[str]:
        """
        Get list of modified contract names.

        Args:
            base_ref: Git base reference for diff.
            head_ref: Git head reference for diff.

        Returns:
            List of contract names (without extension).

        Example:
            >>> contracts = detector.get_modified_contracts()
            >>> print(contracts)
            ["orders_v1", "customers_v1"]
            >>>
            >>> contracts = detector.get_modified_contracts(base_ref="origin/main")
        """
        modified_files = self._git.get_modified_files(base_ref, head_ref)
        return self._filter_contracts(modified_files)

    def _filter_contracts(self, files: list[str]) -> list[str]:
        """
        Filter file list to only contract YAML files.

        Args:
            files: List of file paths.

        Returns:
            List of contract names (without extension).
        """
        contracts = []
        for file_path in files:
            if self._is_contract_file(file_path):
                contracts.append(Path(file_path).stem)
        return contracts

    def _is_contract_file(self, file_path: str) -> bool:
        """
        Check if a file path is a contract file.

        Handles both absolute and relative paths from git diff.

        Args:
            file_path: File path to check (usually relative from git).

        Returns:
            True if file is a contract YAML in contracts directory.
        """
        if not file_path.endswith(self.FILE_EXTENSION):
            return False

        # Convert relative git path to absolute for comparison
        absolute_path = str((Path.cwd() / file_path).resolve())
        return absolute_path.startswith(self._contracts_path)
