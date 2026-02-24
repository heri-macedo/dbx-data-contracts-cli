"""
Publish command - Publish contracts to external catalogs.

CLI commands for publishing data contracts to external systems.

Example:
    $ databricks-contracts publish purview table_name_1
    $ databricks-contracts publish purview table_name_1 table_name_2
    $ databricks-contracts publish purview-modified --base-ref origin/main
"""

from typing import List

import typer

from databricks_contracts.commands.shared.output import print_publish_results

app = typer.Typer(no_args_is_help=True)


@app.command("purview")
def publish_to_purview(
    contracts: List[str] = typer.Argument(
        ...,
        help="Contract names to publish (without .yaml extension)",
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
        help="Preview without actually publishing to Purview",
    ),
) -> None:
    """
    Publish contracts to Microsoft Purview.

    Loads the contract YAMLs, maps them to Purview entity format,
    and publishes to Purview catalog.

    Examples:
        databricks-contracts publish purview table_name_1
        databricks-contracts publish purview table_name_1 table_name_2 table_name_3
        databricks-contracts publish purview table_name_1 --env prod
        databricks-contracts publish purview table_name_1 --dry-run

    Args:
        contracts: List of contract names (without .yaml).
        env: Target environment (dev or prod).
        dry_run: If True, preview without publishing.

    Returns:
        Exit code 0 on success, 1 if any failed.
    """
    from databricks_contracts.handlers import PublishHandler
    from databricks_contracts.models.inputs import PublishInput

    # Create handler with appropriate dependencies
    handler = PublishHandler.create(
        environment=env,
        dry_run=dry_run,
    )

    # Process each contract
    results = []
    for contract_name in contracts:
        input_data = PublishInput(contract_name=contract_name, environment=env)
        result = handler.handle(input_data)
        results.append(result)

    # Output results
    print_publish_results(results, dry_run=dry_run)

    # Exit code based on success
    failed = [r for r in results if not r.success]
    if failed:
        raise typer.Exit(1)


@app.command("purview-modified")
def publish_modified_to_purview(
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
        help="Preview without actually publishing to Purview",
    ),
) -> None:
    """
    Publish modified contracts to Microsoft Purview.

    Detects contracts modified in Git and publishes them to Purview.

    Examples:
        databricks-contracts publish purview-modified
        databricks-contracts publish purview-modified --base-ref origin/main
        databricks-contracts publish purview-modified --env prod
        databricks-contracts publish purview-modified --dry-run

    Args:
        base_ref: Git base reference (default: HEAD~1).
        head_ref: Git head reference (default: HEAD).
        env: Target environment (dev or prod).
        dry_run: If True, preview without publishing.

    Returns:
        Exit code 0 on success, 1 if any failed.
    """
    from databricks_contracts.handlers import PublishHandler

    # Create handler
    handler = PublishHandler.create(
        environment=env,
        dry_run=dry_run,
    )

    # Handle modified contracts
    results = handler.handle_modified(base_ref=base_ref, head_ref=head_ref, environment=env)

    if not results:
        typer.echo("📭 No modified contracts found")
        return

    # Output results
    print_publish_results(results, dry_run=dry_run)

    # Exit code
    failed = [r for r in results if not r.success]
    if failed:
        raise typer.Exit(1)


@app.command("purview-all")
def publish_all_to_purview(
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
        help="Preview without actually publishing to Purview",
    ),
) -> None:
    """
    Publish all contracts to Microsoft Purview.

    Publishes all contracts in the contracts directory to Purview.

    Examples:
        databricks-contracts publish purview-all
        databricks-contracts publish purview-all --env prod
        databricks-contracts publish purview-all --dry-run
    """
    from databricks_contracts.handlers import PublishHandler

    handler = PublishHandler.create(
        environment=env,
        dry_run=dry_run,
    )

    results = handler.handle_all(environment=env)

    if not results:
        typer.echo("📭 No contracts found")
        return

    print_publish_results(results, dry_run=dry_run)

    failed = [r for r in results if not r.success]
    if failed:
        raise typer.Exit(1)
