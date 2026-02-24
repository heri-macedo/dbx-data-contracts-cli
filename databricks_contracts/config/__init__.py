"""
Configuration module.

Provides configuration management:
- settings: Environment variables (Settings)
- project_config: Project configuration from YAML (ProjectConfig)
- constants: Application constants
- logger: Logging utilities

Example:
    >>> from databricks_contracts.config import get_settings, get_logger
    >>> settings = get_settings()
    >>> logger = get_logger(__name__)
"""

from databricks_contracts.config.constants import BundleDefaults, DDLKeywords, Defaults, FileNames
from databricks_contracts.config.logger import get_logger
from databricks_contracts.config.project_config_model import (
    ProjectConfig,
    clear_config_cache,
    load_project_config,
)
from databricks_contracts.config.settings import Settings, clear_settings_cache, get_settings

__all__ = [
    # Settings
    "Settings",
    "get_settings",
    "clear_settings_cache",
    # Project config
    "ProjectConfig",
    "load_project_config",
    "clear_config_cache",
    # Logger
    "get_logger",
    # Constants
    "DDLKeywords",
    "Defaults",
    "FileNames",
    "BundleDefaults",
]
