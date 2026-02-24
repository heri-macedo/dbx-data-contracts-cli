"""
Git services module.

Provides business logic for Git operations:
- ChangeDetectorService: Detect modified contracts

Example:
    >>> from databricks_contracts.services.git import ChangeDetectorService
    >>> detector = ChangeDetectorService.create()
    >>> contracts = detector.get_modified_contracts()
"""

from databricks_contracts.services.git.change_detector import ChangeDetectorService

__all__ = ["ChangeDetectorService"]
