"""
Git adapters module.

Provides adapters for Git operations:
- ChangeDetectorPort: Interface for change detection
- SubprocessGitAdapter: Implementation using subprocess/git CLI

Example:
    >>> from databricks_contracts.adapters.git import SubprocessGitAdapter
    >>> adapter = SubprocessGitAdapter()
    >>> files = adapter.get_modified_files("HEAD~1", "HEAD")
"""

from databricks_contracts.adapters.git.base import ChangeDetectorPort
from databricks_contracts.adapters.git.subprocess_adapter import SubprocessGitAdapter

__all__ = ["ChangeDetectorPort", "SubprocessGitAdapter"]
