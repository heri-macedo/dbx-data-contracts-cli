"""
Purview classification model.

Represents a classification (tag) applied to entities in Azure Purview.

Example:
    >>> from databricks_contracts.models.purview import PurviewClassification
    >>> classification = PurviewClassification(typeName="PII_HIDDEN")
"""

from pydantic import BaseModel, Field


class PurviewClassification(BaseModel):
    """
    Represents a classification in Azure Purview.

    Classifications are used to tag entities with governance metadata
    such as PII levels, business domains, and data layers.

    Attributes:
        typeName: Classification type name as registered in Purview.

    Example:
        >>> classification = PurviewClassification(typeName="PII_HIDDEN")
        >>> classification = PurviewClassification(typeName="Domain_1")
        >>> classification = PurviewClassification(typeName="Layer_3")
    """

    model_config = {"frozen": True}

    typeName: str = Field(
        ...,
        description="Classification type name as registered in Purview",
        examples=["PII_A", "PII_B", "Domain_1", "Layer_3", "Class_C"],
    )
