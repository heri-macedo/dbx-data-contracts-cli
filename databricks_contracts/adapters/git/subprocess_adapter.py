"""
Subprocess Git adapter - Uses git CLI for change detection.

Implements change detection using subprocess to call git commands.

Example:
    >>> from databricks_contracts.adapters.git import SubprocessGitAdapter
    >>> adapter = SubprocessGitAdapter()
    >>> files = adapter.get_modified_files("HEAD~1", "HEAD")
"""

import subprocess

from databricks_contracts.adapters.git.base import ChangeDetectorPort


class SubprocessGitAdapter(ChangeDetectorPort):
    """
    Git adapter using subprocess to run git CLI commands.

    Detects modified files by running `git diff --name-only`.

    Example:
        >>> adapter = SubprocessGitAdapter()
        >>>
        >>> # Get files modified in last commit
        >>> files = adapter.get_modified_files("HEAD~1", "HEAD")
        >>> print(files)
        ["contracts/orders.yaml", "README.md"]
        >>>
        >>> # Get files modified since main branch
        >>> files = adapter.get_modified_files("origin/main", "HEAD")
    """

    def get_modified_files(self, base_ref: str, head_ref: str) -> list[str]:
        """
        Get modified files using git diff command.

        Args:
            base_ref: Base Git reference (e.g., "HEAD~1", "origin/main").
            head_ref: Head Git reference (e.g., "HEAD").

        Returns:
            List of modified file paths. Empty list if git fails.

        Example:
            >>> files = adapter.get_modified_files("HEAD~1", "HEAD")
            >>> print(files)
            ["contracts/orders.yaml", "contracts/customers.yaml"]
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=d", base_ref, head_ref],
                capture_output=True,
                text=True,
                check=True,
            )
            files = result.stdout.strip().split("\n")
            return [f for f in files if f]  # Remove empty strings
        except subprocess.CalledProcessError:
            return []
