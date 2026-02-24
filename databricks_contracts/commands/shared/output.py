"""
Output formatters for CLI.

Provides Rich-based output formatting for CLI results.

Example:
    >>> from databricks_contracts.commands.shared.output import print_run_result
    >>> print_run_result(result)
"""

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from databricks_contracts.models.results import PublishResult, RunResult, TriggerResult, ValidationResult

console = Console()


def print_run_result(result: RunResult) -> None:
    """
    Print apply/run result to console.

    Displays success/failure status followed by any non-fatal warnings
    (e.g. tags that could not be applied due to permission errors).

    Args:
        result: RunResult from ApplyHandler.

    Example:
        >>> print_run_result(result)
        ✅ Applied contract: orders_v1 (3 statements)
           ⚠️  table (classification=Class_1): PERMISSION_DENIED: ...
    """
    if result.success:
        typer.echo(f"✅ Applied contract: {result.contract_name} ({result.statements_count} statements)")
        for warning in result.warnings:
            typer.echo(f"   ⚠️  {warning}")
    else:
        typer.echo(f"❌ Failed: {result.contract_name}")
        if result.error:
            typer.echo(f"   Error: {result.error}")
        for warning in result.warnings:
            typer.echo(f"   ⚠️  {warning}")


def print_publish_result(result: PublishResult, dry_run: bool = False) -> None:
    """
    Print publish result to console.

    Args:
        result: PublishResult from PublishHandler.
        dry_run: Whether this was a dry-run operation.

    Example:
        >>> print_publish_result(result)
        ✅ Published contract: orders_v1
           Collection: DataContracts
           Qualified Name: databricks://catalog.schema.orders
    """
    if result.success:
        if dry_run:
            typer.echo(f"🔶 [DRY-RUN] Would publish contract: {result.contract_name}")
            if result.purview_collection_name:
                typer.echo(f"   Collection: {result.purview_collection_name}")
            if result.purview_qualified_name:
                typer.echo(f"   Qualified Name: {result.purview_qualified_name}")
        else:
            typer.echo(f"✅ Published contract: {result.contract_name}")
            if result.purview_collection_name:
                typer.echo(f"   Collection: {result.purview_collection_name}")
            if result.purview_qualified_name:
                typer.echo(f"   Qualified Name: {result.purview_qualified_name}")
    else:
        typer.echo(f"❌ Failed to publish: {result.contract_name}")
        if result.error:
            typer.echo(f"   Error: {result.error}")


def print_publish_results(results: list[PublishResult], dry_run: bool = False) -> None:
    """
    Print multiple publish results as a table.

    Args:
        results: List of PublishResult from PublishHandler.
        dry_run: Whether this was a dry-run operation.

    Example:
        >>> print_publish_results(results)
        ┌──────────────┬────────┬─────────────────────┐
        │ Contract     │ Status │ Collection          │
        ├──────────────┼────────┼─────────────────────┤
        │ orders_v1    │ ✅     │ DataContracts       │
        └──────────────┴────────┴─────────────────────┘
    """
    if not results:
        typer.echo("No contracts published")
        return

    title = "🔶 Publish Preview (Dry-Run)" if dry_run else "📤 Publish Results"

    table = Table(
        title=title,
        show_header=True,
        header_style="bold",
    )
    table.add_column("Contract", style="cyan")
    table.add_column("Status")
    table.add_column("Collection", style="green")
    table.add_column("Qualified Name / Error", style="yellow", overflow="fold")

    for result in results:
        status = "✅" if result.success else "❌"
        collection = result.purview_collection_name or ""
        qn_or_error = result.purview_qualified_name or result.error or ""
        table.add_row(result.contract_name, status, collection, qn_or_error)

    console.print(table)

    # Summary
    success = sum(1 for r in results if r.success)
    failed = len(results) - success

    if dry_run:
        typer.echo(f"\n🔶 Would publish: {success} contracts")
    else:
        typer.echo(f"\n✅ Published: {success}, ❌ Failed: {failed}")


def print_validation_result(result: ValidationResult) -> None:
    """
    Print single validation result to console.

    Args:
        result: ValidationResult from ValidateHandler.

    Example:
        >>> print_validation_result(result)
        ✅ Contract 'orders_v1' is valid!
    """
    if result.valid:
        typer.echo(f"✅ Contract '{result.contract_name}' is valid!")
    else:
        typer.echo(f"❌ Contract '{result.contract_name}' is invalid")
        if result.error:
            typer.echo(f"   Errors: {result.error}")


def print_validation_results(results: list[ValidationResult]) -> None:
    """
    Print multiple validation results as a table.

    Args:
        results: List of ValidationResult from ValidateHandler.

    Example:
        >>> print_validation_results(results)
        ┌──────────────────┬────────┐
        │ Contract         │ Status │
        ├──────────────────┼────────┤
        │ orders_v1        │ ✅     │
        │ customers_v1     │ ❌     │
        └──────────────────┴────────┘
    """
    if not results:
        typer.echo("No contracts found")
        return

    table = Table(
        title="Validation Results",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Contract", style="cyan")
    table.add_column("Status")
    table.add_column("Errors", style="yellow")

    for result in results:
        status = "✅" if result.valid else "❌"
        errors = str(result.error_count) if result.error_count > 0 else ""
        table.add_row(result.contract_name, status, errors)

    console.print(table)

    # Summary
    valid = sum(1 for r in results if r.valid)
    invalid = len(results) - valid
    typer.echo(f"\nTotal: {valid} valid, {invalid} invalid")

    # Error details
    invalid_results = [r for r in results if not r.valid]
    if invalid_results:
        typer.echo("\n" + "=" * 50)
        typer.echo("📋 Error details:")
        typer.echo("=" * 50)
        for result in invalid_results:
            typer.echo(f"\n{result.contract_name}:")
            if result.error:
                for err in result.error.split("; "):
                    typer.echo(f"  • {err}")


def print_trigger_results(results: list[TriggerResult]) -> None:
    """
    Print trigger results as a table.

    Args:
        results: List of TriggerResult from TriggerHandler.

    Example:
        >>> print_trigger_results(results)
        ┌──────────────┬────────┬───────────┐
        │ Contract     │ Status │ Run ID    │
        ├──────────────┼────────┼───────────┤
        │ orders_v1    │ ✅     │ 123456    │
        └──────────────┴────────┴───────────┘
    """
    if not results:
        typer.echo("No contracts triggered")
        return

    table = Table(
        title="Trigger Results",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Contract", style="cyan")
    table.add_column("Status")
    table.add_column("Run ID", style="green")
    table.add_column("URL/Error", style="yellow", overflow="fold")

    for result in results:
        status = "✅" if result.success else "❌"
        run_id = str(result.run_id) if result.run_id else ""
        url_or_error = result.run_url or result.error or ""
        table.add_row(result.contract_name, status, run_id, url_or_error)

    console.print(table)

    # Summary
    success = sum(1 for r in results if r.success)
    failed = len(results) - success
    typer.echo(f"\nTotal: {success} triggered, {failed} failed")


def format_validation_error(error: ValidationError) -> str:
    """
    Format Pydantic ValidationError as simple text.

    Args:
        error: Pydantic ValidationError.

    Returns:
        Formatted error message.

    Example:
        >>> msg = format_validation_error(error)
        >>> print(msg)
        • table.name: Field required
        • table.columns.0.type: Invalid type
    """
    lines = []
    for err in error.errors():
        field = ".".join(str(x) for x in err["loc"])
        msg = err["msg"]
        lines.append(f"  • {field}: {msg}")
    return "\n".join(lines)


def print_validation_error_rich(error: ValidationError, contract_name: str) -> None:
    """
    Print ValidationError as Rich table.

    Args:
        error: Pydantic ValidationError.
        contract_name: Name of the contract that failed.

    Example:
        >>> print_validation_error_rich(error, "orders")
        ┌──────────────────────────────────────┐
        │ ❌ Validation errors in 'orders'     │
        ├────────────────┬─────────────────────┤
        │ Field          │ Error               │
        ├────────────────┼─────────────────────┤
        │ table.name     │ Field required      │
        └────────────────┴─────────────────────┘
    """
    table = Table(
        title=f"❌ Validation errors in '{contract_name}'",
        title_style="bold red",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Field", style="cyan")
    table.add_column("Error", style="yellow")

    for err in error.errors():
        field = ".".join(str(x) for x in err["loc"])
        msg = err["msg"]
        table.add_row(field, msg)

    console.print()
    console.print(table)
    console.print()
