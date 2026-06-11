"""
Result DTOs from handlers.

Pydantic models that represent operation results.

Example:
    >>> from databricks_contracts.models.results import RunResult, TriggerResult
    >>> result = RunResult(contract_name="test", success=True)
"""

from databricks_contracts.models.results.build_result import EvolutionBuildResult, StatementBuildResult
from databricks_contracts.models.results.execution_result import ExecutionResult
from databricks_contracts.models.results.publish_result import PublishResult
from databricks_contracts.models.results.query_result import QueryResult
from databricks_contracts.models.results.run_result import RunResult
from databricks_contracts.models.results.trigger_result import TriggerResult
from databricks_contracts.models.results.validation_result import ValidationResult

__all__ = [
    "StatementBuildResult",
    "EvolutionBuildResult",
    "PublishResult",
    "RunResult",
    "ValidationResult",
    "TriggerResult",
    "ExecutionResult",
    "QueryResult",
]
