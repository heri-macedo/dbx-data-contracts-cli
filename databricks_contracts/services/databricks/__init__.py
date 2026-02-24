"""
Databricks services module.

Provides business logic for Databricks operations:
- TriggerService: Trigger jobs for contracts

Example:
    >>> from databricks_contracts.services.databricks import TriggerService
    >>> service = TriggerService.create()
    >>> result = service.trigger("orders_v1")
"""

from databricks_contracts.services.databricks.trigger import TriggerService

__all__ = ["TriggerService"]
