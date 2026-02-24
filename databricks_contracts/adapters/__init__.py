"""
Adapters module - External system integrations.

This module provides adapters for interacting with external systems:
- databricks/: Databricks API client, job generator, and SQL executors
- git/: Git operations for change detection

Example:
    >>> from databricks_contracts.adapters import DatabricksClient, SparkExecutor
    >>> from databricks_contracts.adapters.git import SubprocessGitAdapter
"""

# Databricks adapters
from databricks_contracts.adapters.databricks.api_client import DatabricksClient
from databricks_contracts.adapters.databricks.executors import (
    BaseExecutor,
    DryRunExecutor,
    SparkExecutor,
)
from databricks_contracts.adapters.databricks.job_generator import ContractJobGenerator

# Git adapters
from databricks_contracts.adapters.git.base import ChangeDetectorPort
from databricks_contracts.adapters.git.subprocess_adapter import SubprocessGitAdapter

__all__ = [
    # Databricks
    "DatabricksClient",
    "ContractJobGenerator",
    "BaseExecutor",
    "DryRunExecutor",
    "SparkExecutor",
    # Git
    "ChangeDetectorPort",
    "SubprocessGitAdapter",
]
