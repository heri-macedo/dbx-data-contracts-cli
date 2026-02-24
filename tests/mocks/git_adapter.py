"""
Mock Git adapter for testing.

Provides a controllable adapter that returns predefined file lists.

Example:
    >>> from tests.mocks import MockGitAdapter
    >>> adapter = MockGitAdapter(["contracts/test.yaml"])
    >>> files = adapter.get_modified_files("HEAD~1", "HEAD")
    >>> print(files)
    ["contracts/test.yaml"]
"""

from databricks_contracts.adapters.git.base import ChangeDetectorPort


class MockGitAdapter(ChangeDetectorPort):
    """
    Mock Git adapter for testing.

    Returns a predefined list of modified files regardless of input.
    Useful for unit testing services that depend on Git.

    Attributes:
        modified_files: List of files to return.

    Example:
        >>> # Create adapter with predefined files
        >>> adapter = MockGitAdapter([
        ...     "contracts/orders.yaml",
        ...     "contracts/customers.yaml",
        ...     "README.md",
        ... ])
        >>>
        >>> # Use in tests
        >>> files = adapter.get_modified_files("any", "ref")
        >>> assert "contracts/orders.yaml" in files
    """

    def __init__(self, modified_files: list[str] | None = None) -> None:
        """
        Initialize the mock adapter.

        Args:
            modified_files: List of file paths to return. Defaults to empty list.

        Example:
            >>> adapter = MockGitAdapter(["file1.yaml", "file2.yaml"])
            >>> adapter = MockGitAdapter()  # Empty list
        """
        self._modified_files = modified_files or []

    def get_modified_files(self, base_ref: str, head_ref: str) -> list[str]:
        """
        Return the predefined list of modified files.

        Args:
            base_ref: Ignored in mock.
            head_ref: Ignored in mock.

        Returns:
            Predefined list of file paths.

        Example:
            >>> adapter = MockGitAdapter(["test.yaml"])
            >>> adapter.get_modified_files("ignored", "also_ignored")
            ["test.yaml"]
        """
        return self._modified_files
