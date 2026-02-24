"""
Project configuration - Loads datacontract.config.yaml.

Composition of names:
    catalog = domain.name + environments.{env}.catalog_suffix
    schema  = domain.sub_domain

Example:
    dev:  "test_catalog" + "" = "test_catalog"
    prod: "test_catalog" + "_prod" = "test_catalog_prod"

Example:
    >>> from databricks_contracts.config import load_project_config
    >>> config = load_project_config()
    >>> print(config.get_catalog("prod"))
    "test_catalog_prod"
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

from databricks_contracts.config.constants import FileNames
from databricks_contracts.exceptions import ProjectConfigNotFoundError


class DomainConfig(BaseModel):
    """
    Domain configuration.

    Attributes:
        name: Used as catalog base (Unity Catalog catalog).
        sub_domain: Used as schema (Unity Catalog schema).
        description: Optional domain description.

    Example:
        >>> domain = DomainConfig(
        ...     name="test_catalog",
        ...     sub_domain="test_schema",
        ...     description="Test domain",
        ... )
    """

    model_config = {"frozen": True}

    name: str = Field(
        ...,
        description="Catalog base name (Unity Catalog)",
        examples=["test_catalog", "analytics"],
    )
    sub_domain: str = Field(
        ...,
        description="Schema name (Unity Catalog)",
        examples=["test_schema", "trading"],
    )
    description: str = Field(
        default="",
        description="Domain description",
    )


class EnvironmentConfig(BaseModel):
    """
    Environment-specific configuration.

    Attributes:
        catalog_suffix: Suffix to append to catalog name.

    Example:
        >>> env = EnvironmentConfig(catalog_suffix="_prod")
    """

    model_config = {"frozen": True}

    catalog_suffix: str = Field(
        default="",
        description="Suffix to append to catalog name",
        examples=["", "_prod", "_dev"],
    )


class OwnershipConfig(BaseModel):
    """
    Default ownership configuration.

    Optional defaults that can be overridden per-contract.

    Attributes:
        data_owner: Default data owner.
        bds: Default Business Data Steward.
        tds: Default Technical Data Steward.
        purview_collection: Default Purview collection.

    Example:
        >>> ownership = OwnershipConfig(
        ...     data_owner="team@example.com",
        ...     bds="bds@example.com",
        ... )
    """

    model_config = {"frozen": True}

    data_owner: Optional[str] = None
    bds: Optional[str] = None
    tds: Optional[str] = None
    purview_collection: Optional[str] = None


class AllowedValuesConfig(BaseModel):
    """
    Allowed values for tags (for validation).

    Attributes:
        layer: Allowed layer values.
        classification: Allowed classification values.
        portfolio: Allowed portfolio values.

    Example:
        >>> allowed = AllowedValuesConfig(
        ...     layer=["Bronze", "Silver", "Gold"],
        ... )
    """

    model_config = {"frozen": True, "populate_by_name": True}

    layer: Optional[list[str]] = Field(default=None, alias="camada")
    classification: Optional[list[str]] = Field(default=None, alias="classificacao")
    portfolio: Optional[list[str]] = Field(default=None)


class ValidationConfig(BaseModel):
    """
    Validation configuration.

    Attributes:
        enforce_catalog: Enforce catalog matches domain.
        enforce_schema: Enforce schema matches domain.
        allowed_values: Allowed values for tags.

    Example:
        >>> validation = ValidationConfig(
        ...     enforce_catalog=True,
        ...     enforce_schema=True,
        ... )
    """

    model_config = {"frozen": True}

    enforce_catalog: bool = Field(
        default=True,
        description="Enforce catalog matches domain",
    )
    enforce_schema: bool = Field(
        default=True,
        description="Enforce schema matches domain",
    )
    allowed_values: Optional[AllowedValuesConfig] = None


class EnvironmentsConfig(BaseModel):
    """
    Environment-specific configurations.

    Attributes:
        dev: Development environment configuration.
        prod: Production environment configuration.

    Example:
        >>> envs = EnvironmentsConfig(
        ...     dev=EnvironmentConfig(catalog_suffix=""),
        ...     prod=EnvironmentConfig(catalog_suffix="_prod"),
        ... )
    """

    model_config = {"frozen": True}

    dev: EnvironmentConfig = Field(
        default_factory=lambda: EnvironmentConfig(catalog_suffix=""),
        description="Development environment configuration",
    )
    prod: EnvironmentConfig = Field(
        default_factory=lambda: EnvironmentConfig(catalog_suffix="_prod"),
        description="Production environment configuration",
    )


class ProjectConfig(BaseModel):
    """
    Project configuration loaded from datacontract.config.yaml.

    This file should be placed at the root of the contracts repository.

    Catalog resolution:
        catalog = domain.name + environments.{env}.catalog_suffix

    Attributes:
        domain: Domain configuration (name, sub_domain).
        environments: Environment-specific settings.
        ownership: Default ownership values.
        validation: Validation settings.

    Example:
        >>> config = ProjectConfig.model_validate(yaml_data)
        >>> print(config.get_catalog("prod"))
        "test_catalog_prod"
        >>> print(config.schema_name)
        "test_schema"
    """

    model_config = {"frozen": True, "populate_by_name": True}

    domain: DomainConfig = Field(
        ...,
        description="Domain configuration",
    )
    environments: EnvironmentsConfig = Field(
        default_factory=EnvironmentsConfig,
        description="Environment-specific configurations",
    )
    ownership: Optional[OwnershipConfig] = Field(
        default=None,
        description="Default ownership values",
    )
    validation: ValidationConfig = Field(
        default_factory=ValidationConfig,
        description="Validation configuration",
    )

    def get_catalog(self, environment: str) -> str:
        """
        Resolve catalog name for a given environment.

        Composition: domain.name + environments.{env}.catalog_suffix

        Args:
            environment: Environment name (dev, prod).

        Returns:
            Resolved catalog name.

        Example:
            >>> config.get_catalog("dev")
            "test_catalog"
            >>> config.get_catalog("prod")
            "test_catalog_prod"
        """
        env_settings = getattr(self.environments, environment.lower(), self.environments.dev)
        return f"{self.domain.name}{env_settings.catalog_suffix}"

    @property
    def schema_name(self) -> str:
        """
        Get schema name from domain.sub_domain.

        Returns:
            Schema name.

        Example:
            >>> config.schema_name
            "test_schema"
        """
        return self.domain.sub_domain


def _find_config_file() -> Path:
    """
    Find the project config file.

    Searches upward from cwd for datacontract.config.yaml.

    Returns:
        Path to config file.

    Raises:
        ProjectConfigNotFoundError: If not found.
    """
    current = Path.cwd()
    max_levels = 5

    for _ in range(max_levels):
        candidate = current / FileNames.PROJECT_CONFIG
        if candidate.exists():
            return candidate
        if current.parent == current:
            break
        current = current.parent

    # Fallback
    fallback = Path.cwd() / FileNames.PROJECT_CONFIG
    if fallback.exists():
        return fallback

    raise ProjectConfigNotFoundError(
        f"Required config file not found: {FileNames.PROJECT_CONFIG}\n"
        f"Create a '{FileNames.PROJECT_CONFIG}' file in your project root."
    )


@lru_cache(maxsize=1)
def load_project_config() -> ProjectConfig:
    """
    Load project configuration from datacontract.config.yaml.

    The config file is required and must be in the repository root.
    Uses lru_cache to avoid re-reading the file.

    Returns:
        ProjectConfig instance.

    Raises:
        ProjectConfigNotFoundError: If config file is not found.

    Example:
        >>> config = load_project_config()
        >>> print(config.get_catalog("prod"))
    """
    config_path = _find_config_file()

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return ProjectConfig.model_validate(data)


def clear_config_cache() -> None:
    """
    Clear the cached configuration.

    Useful for tests that need to reload config.

    Example:
        >>> clear_config_cache()
        >>> config = load_project_config()  # Reloads from disk
    """
    load_project_config.cache_clear()
