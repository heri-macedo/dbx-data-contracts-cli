"""
Input DTOs for handlers.

Pydantic models that define and validate inputs for CLI handlers.

Example:
    >>> from databricks_contracts.models.inputs import ApplyInput
    >>> input = ApplyInput(contract_name="my_contract", environment="prod")
"""

from databricks_contracts.models.inputs.apply_input import ApplyInput
from databricks_contracts.models.inputs.publish_input import PublishInput
from databricks_contracts.models.inputs.trigger_input import TriggerInput
from databricks_contracts.models.inputs.validate_input import ValidateInput

__all__ = ["ApplyInput", "PublishInput", "ValidateInput", "TriggerInput"]
