"""
Databricks adapters module.

Provides integration with Databricks services:
- api_client: Jobs API client for triggering jobs
- job_generator: DAB job configuration generator
- executors/: SQL execution strategies (Spark, DryRun)

Example:
    >>> from databricks_contracts.adapters.databricks import DatabricksClient
    >>> client = DatabricksClient()
    >>> job_id = client.find_job_by_name("Apply Contract")
"""

from databricks_contracts.adapters.databricks.api_client import DatabricksClient
from databricks_contracts.adapters.databricks.executors import (
    BaseExecutor,
    DryRunExecutor,
    SparkExecutor,
)
from databricks_contracts.adapters.databricks.job_generator import ContractJobGenerator

__all__ = [
    "DatabricksClient",
    "ContractJobGenerator",
    "BaseExecutor",
    "DryRunExecutor",
    "SparkExecutor",
]
