"""
DDL executors for Databricks.

Provides different strategies for executing DDL statements:
- SparkExecutor: Executes via SparkSession (production)
- DryRunExecutor: Prints DDL without executing (preview)

Example:
    >>> from databricks_contracts.adapters.databricks.executors import SparkExecutor
    >>> executor = SparkExecutor()
    >>> result = executor.execute(statement)
"""

from databricks_contracts.adapters.databricks.executors.base import BaseExecutor
from databricks_contracts.adapters.databricks.executors.dry_run import DryRunExecutor
from databricks_contracts.adapters.databricks.executors.spark import SparkExecutor

__all__ = ["BaseExecutor", "DryRunExecutor", "SparkExecutor"]
