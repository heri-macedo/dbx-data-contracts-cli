"""
Purview entity models for Azure Purview API integration.

Pydantic models representing Purview/Atlas entities for catalog operations.

Example:
    >>> from databricks_contracts.models.purview import PurviewEntity
    >>> entity = PurviewEntity(...)
    >>> payload = entity.to_json()
"""

from databricks_contracts.models.purview.classification import PurviewClassification
from databricks_contracts.models.purview.column import PurviewColumnAttributes, PurviewColumnEntity
from databricks_contracts.models.purview.entity import PurviewTableAttributes, PurviewTableEntity

__all__ = [
    "PurviewClassification",
    "PurviewColumnAttributes",
    "PurviewColumnEntity",
    "PurviewTableAttributes",
    "PurviewTableEntity",
]
