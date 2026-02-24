"""
Environment variables configuration using Pydantic BaseSettings.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables:
        DATABRICKS_HOST: Databricks workspace URL
        DATABRICKS_CLIENT_ID: Service principal client ID
        DATABRICKS_CLIENT_SECRET: Service principal client secret
        ENVIRONMENT: Target environment (dev, prod)
        CONTRACTS_PATH: Path to contracts directory (optional override)
        PURVIEW_ACCOUNT_NAME: Microsoft Purview account name
        PURVIEW_CLIENT_ID: Azure AD application client ID for Purview
        PURVIEW_CLIENT_SECRET: Azure AD application client secret for Purview
        PURVIEW_TENANT_ID: Azure AD tenant ID for Purview
    """

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Databricks connection
    DATABRICKS_HOST: Optional[str] = Field(
        default=None,
        description="Databricks workspace URL",
    )
    DATABRICKS_CLIENT_ID: Optional[str] = Field(
        default=None,
        description="Service principal client ID",
    )
    DATABRICKS_CLIENT_SECRET: Optional[SecretStr] = Field(
        default=None,
        description="Service principal client secret",
    )

    # Microsoft Purview connection
    PURVIEW_ACCOUNT_NAME: Optional[str] = Field(
        default=None,
        description="Microsoft Purview account name (without .purview.azure.com)",
    )
    PURVIEW_CLIENT_ID: Optional[str] = Field(
        default=None,
        description="Azure AD application client ID for Purview authentication",
    )
    PURVIEW_CLIENT_SECRET: Optional[SecretStr] = Field(
        default=None,
        description="Azure AD application client secret for Purview authentication",
    )
    PURVIEW_TENANT_ID: Optional[str] = Field(
        default=None,
        description="Azure AD tenant ID for Purview authentication",
    )
    PURVIEW_QUALIFIED_NAME_PREFIX: str = Field(
        default="databricks://metastore/",
        description="Prefix for Purview qualified names (matching Databricks UC scan format)",
    )
    PURVIEW_TABLE_TYPE_NAME: str = Field(
        default="databricks_table",
        description="Purview entity type for tables (e.g., databricks_table, azure_sql_table)",
    )
    PURVIEW_COLUMN_TYPE_NAME: str = Field(
        default="databricks_table_column",
        description="Purview entity type for columns (e.g., databricks_table_column, azure_sql_column)",
    )

    # Environment
    ENVIRONMENT: str = Field(
        default="dev",
        description="Target environment (dev, prod)",
    )

    # Paths
    PROJECT_ROOT: Optional[str] = Field(
        default=None,
        description="Project root path (for Databricks jobs)",
    )
    CONTRACTS_PATH: str = Field(
        default="data_contracts/assets",
        description="Path to contracts directory",
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "prod"

    @property
    def has_purview_configuration(self) -> bool:
        """Check if Purview configuration is complete."""
        return all(
            [
                self.PURVIEW_ACCOUNT_NAME,
                self.PURVIEW_CLIENT_ID,
                self.PURVIEW_CLIENT_SECRET,
                self.PURVIEW_TENANT_ID,
            ]
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get or create settings instance (cached)."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear the cached settings (for tests)."""
    get_settings.cache_clear()
