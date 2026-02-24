"""
Trigger command - Trigger Databricks jobs.

CLI commands for triggering Databricks jobs.

Example:
    $ databricks-contracts trigger contracts orders_v1 customers_v1
    $ databricks-contracts trigger modified --base-ref origin/main
"""

from typing import List

import typer

from databricks_contracts.commands.shared.output import print_trigger_results

app = typer.Typer(no_args_is_help=True)


@app.command("contracts")
def trigger_contracts(
    contracts: List[str] = typer.Argument(
        ...,
        help="Contract names to trigger jobs for",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Preview without triggering",
    ),
) -> None:
    """
    Trigger jobs for specific contracts.

    Finds and triggers Databricks jobs for the given contracts.

    Examples:
        databricks-contracts trigger contracts orders_v1
        databricks-contracts trigger contracts orders_v1 customers_v1
        databricks-contracts trigger contracts orders_v1 --dry-run

    Args:
        contracts: List of contract names to trigger.
        dry_run: If True, don't actually trigger jobs.

    Returns:
        Exit code 0 on success, 1 if any failed.
    """
    from databricks_contracts.handlers import TriggerHandler
    from databricks_contracts.models.inputs import TriggerInput

    # Create handler
    handler = TriggerHandler.create(dry_run=dry_run)

    # Build input
    input = TriggerInput(contracts=list(contracts))

    # Handle
    results = handler.handle(input)

    # Output
    print_trigger_results(results)

    # Exit code
    failed = [r for r in results if not r.success]
    if failed:
        raise typer.Exit(1)


@app.command("modified")
def trigger_modified(
    base_ref: str = typer.Option(
        "HEAD~1",
        "--base-ref",
        "-b",
        help="Git base reference for diff",
    ),
    head_ref: str = typer.Option(
        "HEAD",
        "--head-ref",
        help="Git head reference for diff",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Preview without triggering",
    ),
) -> None:
    """
    Trigger jobs for modified contracts.

    Detects contracts modified in Git and triggers their jobs.

    Examples:
        databricks-contracts trigger modified
        databricks-contracts trigger modified --base-ref origin/main
        databricks-contracts trigger modified --dry-run

    Args:
        base_ref: Git base reference (default: HEAD~1).
        head_ref: Git head reference (default: HEAD).
        dry_run: If True, don't actually trigger jobs.

    Returns:
        Exit code 0 on success, 1 if any failed.
    """
    from databricks_contracts.handlers import TriggerHandler

    # Create handler
    handler = TriggerHandler.create(dry_run=dry_run)

    # Handle modified
    results = handler.handle_modified(base_ref=base_ref, head_ref=head_ref)

    if not results:
        typer.echo("No modified contracts found")
        return

    # Output
    print_trigger_results(results)

    # Exit code
    failed = [r for r in results if not r.success]
    if failed:
        raise typer.Exit(1)


@app.command("all")
def trigger_all(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Preview without triggering",
    ),
) -> None:
    """
    Trigger jobs for all contracts.

    Triggers jobs for all contracts in the contracts directory.

    Examples:
        databricks-contracts trigger all
        databricks-contracts trigger all --dry-run
    """
    from databricks_contracts.handlers import TriggerHandler

    handler = TriggerHandler.create(dry_run=dry_run)
    results = handler.handle_all()

    if not results:
        typer.echo("No contracts found")
        return

    print_trigger_results(results)

    failed = [r for r in results if not r.success]
    if failed:
        raise typer.Exit(1)
