"""
Ownership model for governance information.

Defines data ownership, stewardship, and governance metadata
required for data contracts.

Example:
    >>> from databricks_contracts.models.contracts import Ownership
    >>> from databricks_contracts.models.contracts.enums import Portfolio, SubDomain
    >>>
    >>> ownership = Ownership(
    ...     data_owner="john.doe@company.com",
    ...     bds="jane.smith@company.com",
    ...     tds="tech.lead@company.com",
    ...     purview_collection="TestCollection",
    ...     portfolio=Portfolio.PORTFOLIO_1,
    ...     sub_domain=SubDomain.SUB_DOMAIN_1,
    ...     business_description="Test business description",
    ... )
"""

from pydantic import BaseModel, Field

from databricks_contracts.models.contracts.enums import Portfolio, SubDomain


class Ownership(BaseModel):
    """
    Ownership and governance information for a data contract.

    All fields are required as per Data Contract Flex specification.

    Attributes:
        data_owner: Email/identifier of the data owner.
        bds: Business Data Steward email/identifier.
        tds: Technical Data Steward email/identifier.
        purview_collection: Microsoft Purview collection name.
        portfolio: Portfolio classification.
        sub_domain: Sub domain identifier.
        business_description: Business description.

    Example:
        >>> ownership = Ownership(
        ...     data_owner="owner@example.com",
        ...     bds="bds@example.com",
        ...     tds="tds@example.com",
        ...     purview_collection="TestCollection",
        ...     portfolio=Portfolio.PORTFOLIO_1,
        ...     sub_domain=SubDomain.SUB_DOMAIN_1,
        ...     business_description="Test business description",
        ... )
    """

    model_config = {"frozen": True, "extra": "forbid"}

    data_owner: str = Field(
        ...,
        description="Data owner email/identifier",
        examples=["john.doe@example.com"],
    )
    bds: str = Field(
        ...,
        description="Business Data Steward email/identifier",
        examples=["jane.smith@example.com"],
    )
    tds: str = Field(
        ...,
        description="Technical Data Steward email/identifier",
        examples=["tech.lead@example.com"],
    )
    purview_collection: str = Field(
        ...,
        description="Microsoft Purview collection name",
        examples=["TestCollection"],
    )
    portfolio: Portfolio = Field(
        ...,
        description="Portfolio classification",
        examples=["Portfolio_1", "Portfolio_2"],
    )
    sub_domain: SubDomain = Field(
        ...,
        description="Sub domain identifier",
        examples=["SubDomain_1", "SubDomain_2"],
    )
    business_description: str = Field(
        ...,
        description="Business description of the data",
        examples=["Business description for test data"],
    )
