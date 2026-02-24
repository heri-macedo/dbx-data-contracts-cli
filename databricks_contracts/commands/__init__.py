"""
Commands module - CLI layer.

This module provides the CLI interface using Typer:
- apply: Apply contracts to Unity Catalog
- validate: Validate contract YAML files
- trigger: Trigger Databricks jobs

Example:
    >>> databricks-contracts apply contract orders_v1
    >>> databricks-contracts validate all
    >>> databricks-contracts trigger modified
"""

from databricks_contracts.commands.main import app

__all__ = ["app"]
