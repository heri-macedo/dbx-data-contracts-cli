"""
Apply command - Apply contracts to Unity Catalog.

CLI commands for applying data contracts.

Example:
    $ databricks-contracts apply contract orders_v1
    $ databricks-contracts apply contract orders_v1 --env prod
    $ databricks-contracts apply contract orders_v1 --dry-run
"""

import os
from typing import Optional

import typer

from databricks_contracts.commands.shared.output import print_run_result

app = typer.Typer(no_args_is_help=True)


@app.command("contract")
def apply_contract(
    contract_name: str = typer.Argument(
        ...,
        help="Contract name (without .yaml extension)",
    ),
    env: str = typer.Option(
        "dev",
        "--env",
        "-e",
        help="Target environment (dev, prod)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Preview DDL without executing",
    ),
    workflow_sp_id: Optional[str] = typer.Option(
        None,
        "--workflow-sp-id",
        hidden=True,
        help="Service Principal ID for GRANT (internal use by Databricks jobs)",
    ),
) -> None:
    """
    Apply a single contract to Unity Catalog.

    Loads the contract YAML, generates DDL, and executes it.

    Examples:
        databricks-contracts apply contract orders_v1
        databricks-contracts apply contract orders_v1 --env prod
        databricks-contracts apply contract orders_v1 --dry-run

    Args:
        contract_name: Name of the contract (without .yaml).
        env: Target environment (dev or prod).
        dry_run: If True, preview DDL without executing.

    Returns:
        Exit code 0 on success, 1 on failure.
    """
    # Set WORKFLOW_SP_ID as env var if provided (for Databricks jobs)
    if workflow_sp_id:
        os.environ["WORKFLOW_SP_ID"] = workflow_sp_id

    from databricks_contracts.handlers import ApplyHandler
    from databricks_contracts.models.inputs import ApplyInput

    # Create handler
    handler = ApplyHandler.create(environment=env, dry_run=dry_run)

    # Build input
    input = ApplyInput(contract_name=contract_name, environment=env)

    # Handle
    result = handler.handle(input)

    # Output
    print_run_result(result)

    # Exit code
    if not result.success:
        raise typer.Exit(1)
