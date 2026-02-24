"""
Validate command - Validate contract YAML files.

CLI commands for validating data contracts.

Example:
    $ databricks-contracts validate contract orders_v1
    $ databricks-contracts validate all
"""

import typer

from databricks_contracts.commands.shared.output import print_validation_result, print_validation_results

app = typer.Typer(no_args_is_help=True)


@app.command("contract")
def validate_contract(
    contract_name: str = typer.Argument(
        ...,
        help="Contract name (without .yaml extension)",
    ),
) -> None:
    """
    Validate a single contract file.

    Checks if the contract YAML is valid against the schema.

    Examples:
        databricks-contracts validate contract orders_v1
        databricks-contracts validate contract customers.yaml

    Args:
        contract_name: Name of the contract (without .yaml).

    Returns:
        Exit code 0 if valid, 1 if invalid.
    """
    from databricks_contracts.handlers import ValidateHandler
    from databricks_contracts.models.inputs import ValidateInput

    # Create handler
    handler = ValidateHandler.create()

    # Build input
    input = ValidateInput(contract_name=contract_name)

    # Handle
    result = handler.handle(input)

    # Output (single result)
    if not isinstance(result, list):
        print_validation_result(result)

        if not result.valid:
            raise typer.Exit(1)


@app.command("all")
def validate_all() -> None:
    """
    Validate all contract files.

    Checks all contracts in the contracts directory.

    Examples:
        databricks-contracts validate all

    Returns:
        Exit code 0 if all valid, 1 if any invalid.
    """
    from databricks_contracts.handlers import ValidateHandler
    from databricks_contracts.models.inputs import ValidateInput

    # Create handler
    handler = ValidateHandler.create()

    # Build input
    input = ValidateInput()

    # Handle
    results = handler.handle(input)

    # Output (list of results)
    if isinstance(results, list):
        print_validation_results(results)

        # Check for invalid
        invalid = [r for r in results if not r.valid]
        if invalid:
            raise typer.Exit(1)
