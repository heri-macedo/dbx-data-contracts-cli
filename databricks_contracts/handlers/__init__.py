"""
Handlers module - Orchestration layer.

This module provides handlers that orchestrate business operations:
- ApplyHandler: Orchestrates contract application
- ValidateHandler: Orchestrates contract validation
- TriggerHandler: Orchestrates job triggering
- PublishHandler: Orchestrates contract publishing to Purview

Example:
    >>> from databricks_contracts.handlers import ApplyHandler
    >>> from databricks_contracts.models.inputs import ApplyInput
    >>>
    >>> handler = ApplyHandler.create()
    >>> result = handler.handle(ApplyInput(contract_name="orders"))
"""

from databricks_contracts.handlers.apply_handler import ApplyHandler
from databricks_contracts.handlers.publish_handler import PublishHandler
from databricks_contracts.handlers.trigger_handler import TriggerHandler
from databricks_contracts.handlers.validate_handler import ValidateHandler

__all__ = ["ApplyHandler", "PublishHandler", "ValidateHandler", "TriggerHandler"]
