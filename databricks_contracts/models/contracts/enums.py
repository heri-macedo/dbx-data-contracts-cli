"""
Contract domain enums.

Defines allowed values for contract fields used in Unity Catalog.

Example:
    >>> from databricks_contracts.models.contracts.enums import ContractStatus, Layer
    >>> status = ContractStatus.ACTIVE
    >>> layer = Layer.LAYER_3
"""

from enum import Enum


class ContractStatus(str, Enum):
    """
    Contract lifecycle status.

    Attributes:
        DRAFT: Contract is being developed, not yet active.
        ACTIVE: Contract is active and being used.
        DEPRECATED: Contract is deprecated and should not be used.

    Example:
        >>> status = ContractStatus.ACTIVE
        >>> print(status.value)  # "active"
    """

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class RefreshFrequency(str, Enum):
    """
    Data refresh frequency options for table metadata.

    Attributes:
        REALTIME: Data is refreshed in real-time.
        HOURLY: Data is refreshed every hour.
        DAILY: Data is refreshed daily.
        WEEKLY: Data is refreshed weekly.
        MONTHLY: Data is refreshed monthly.

    Example:
        >>> freq = RefreshFrequency.DAILY
        >>> print(freq.value)  # "daily"
    """

    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Layer(str, Enum):
    """
    Data layer classification for Unity Catalog table tags.

    Attributes:
        ADMIN: Configuration/Admin layer.
        BRONZE: Raw data layer.
        SILVER: Cleansed data layer.
        GOLD: Business-ready data layer.

    Example:
        >>> layer = Layer.GOLD
        >>> print(layer.value)  # "Gold"
    """

    ADMIN = "Admin"
    BRONZE = "Bronze"
    SILVER = "Silver"
    GOLD = "Gold"


class Classification(str, Enum):
    """
    Data classification tags for governance.

    Attributes:
        CLASSIFICATION_1: Classification 1.
        CLASSIFICATION_2: Classification 2.
        CLASSIFICATION_3: Classification 3.
        CLASSIFICATION_4: Classification 4.

    Example:
        >>> classification = Classification.CLASSIFICATION_1
        >>> print(classification.value)  # "Classification_1"
    """

    CLASSIFICATION_1 = "Classification_1"
    CLASSIFICATION_2 = "Classification_2"
    CLASSIFICATION_3 = "Classification_3"
    CLASSIFICATION_4 = "Classification_4"


class Portfolio(str, Enum):
    """
    Portfolio tags for classification.

    Attributes:
        PORTFOLIO_1: Portfolio 1.
        PORTFOLIO_2: Portfolio 2.
        PORTFOLIO_3: Portfolio 3.
        PORTFOLIO_4: Portfolio 4.
        PORTFOLIO_5: Portfolio 5.
        PORTFOLIO_6: Portfolio 6.
        PORTFOLIO_7: Portfolio 7.
        PORTFOLIO_8: Portfolio 8.
        PORTFOLIO_9: Portfolio 9.
        PORTFOLIO_10: Portfolio 10.

    Example:
        >>> portfolio = Portfolio.PORTFOLIO_1
        >>> print(portfolio.value)  # "Portfolio_1"
    """

    PORTFOLIO_1 = "Portfolio_1"
    PORTFOLIO_2 = "Portfolio_2"
    PORTFOLIO_3 = "Portfolio_3"
    PORTFOLIO_4 = "Portfolio_4"
    PORTFOLIO_5 = "Portfolio_5"
    PORTFOLIO_6 = "Portfolio_6"
    PORTFOLIO_7 = "Portfolio_7"
    PORTFOLIO_8 = "Portfolio_8"
    PORTFOLIO_9 = "Portfolio_9"
    PORTFOLIO_10 = "Portfolio_10"


class SubDomain(str, Enum):
    """
    SubDomain tags for classification.

    Example:
        >>> subdomain = SubDomain.SUB_DOMAIN_1
        >>> print(subdomain.value)  # "Sub_Domain_1"
    """

    SUB_DOMAIN_1 = "Sub_Domain_1"
    SUB_DOMAIN_2 = "Sub_Domain_2"
    SUB_DOMAIN_3 = "Sub_Domain_3"
    SUB_DOMAIN_4 = "Sub_Domain_4"
    SUB_DOMAIN_5 = "Sub_Domain_5"
    SUB_DOMAIN_6 = "Sub_Domain_6"
    SUB_DOMAIN_7 = "Sub_Domain_7"
    SUB_DOMAIN_8 = "Sub_Domain_8"
    SUB_DOMAIN_9 = "Sub_Domain_9"
    SUB_DOMAIN_10 = "Sub_Domain_10"


class Privacy(str, Enum):
    """
    Privacy/PII tags for column-level governance.

    Attributes:
        PII_HIDDEN: PII data that should be hidden.
        PII_ENCRYPTED: PII data that is encrypted.

    Example:
        >>> privacy = Privacy.PII_HIDDEN
        >>> print(privacy.value)  # "PII_HIDDEN"
    """

    PII_HIDDEN = "PII_HIDDEN"
    PII_ENCRYPTED = "PII_ENCRYPTED"
