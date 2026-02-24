"""
Shared utilities for CLI commands.

Provides common output formatters and helpers.

Example:
    >>> from databricks_contracts.commands.shared import print_run_result
    >>> print_run_result(result)
"""

from databricks_contracts.commands.shared.output import (
    format_validation_error,
    print_run_result,
    print_trigger_results,
    print_validation_error_rich,
    print_validation_result,
    print_validation_results,
)

__all__ = [
    "print_run_result",
    "print_validation_result",
    "print_validation_results",
    "print_trigger_results",
    "format_validation_error",
    "print_validation_error_rich",
]
