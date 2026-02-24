"""
Git change detector interface.

Defines the contract for Git adapters that detect file changes.

Example:
    >>> from databricks_contracts.adapters.git import ChangeDetectorPort
    >>>
    >>> class MyGitAdapter(ChangeDetectorPort):
    ...     def get_modified_files(self, base_ref, head_ref):
    ...         # Custom implementation
    ...         return ["file1.yaml", "file2.yaml"]
"""

from abc import ABC, abstractmethod


class ChangeDetectorPort(ABC):
    """
    Interface for Git change detection adapters.

    Defines the contract for detecting modified files between Git references.
    Implementations can use subprocess, GitHub API, or other methods.

    Example:
        >>> class GitHubAdapter(ChangeDetectorPort):
        ...     def get_modified_files(self, base_ref, head_ref):
        ...         # Use GitHub API to get changed files
        ...         return self._github_client.compare(base_ref, head_ref)
    """

    @abstractmethod
    def get_modified_files(self, base_ref: str, head_ref: str) -> list[str]:
        """
        Get list of modified files between two Git references.

        Args:
            base_ref: Base Git reference (e.g., "HEAD~1", "origin/main").
            head_ref: Head Git reference (e.g., "HEAD").

        Returns:
            List of file paths that were modified.

        Example:
            >>> files = adapter.get_modified_files("HEAD~1", "HEAD")
            >>> print(files)
            ["contracts/orders.yaml", "contracts/customers.yaml", "README.md"]
        """
        pass
