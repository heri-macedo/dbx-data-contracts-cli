"""
Main CLI application - Entry point and command router.

Registers all subcommands and provides the main CLI app.

Example:
    $ databricks-contracts --help
    $ databricks-contracts apply contract orders_v1
    $ databricks-contracts validate all
    $ databricks-contracts publish contract orders_v1
"""

import typer

from databricks_contracts.commands import apply, publish, trigger, validate

# Main CLI app
app = typer.Typer(
    name="databricks-contracts",
    help="Databricks Data Contracts CLI - Apply data contracts to Unity Catalog.",
    no_args_is_help=True,
    add_completion=False,
)

# Register subcommands
app.add_typer(apply.app, name="apply", help="Apply contracts to Unity Catalog")
app.add_typer(publish.app, name="publish", help="Publish contracts to Microsoft Purview")
app.add_typer(validate.app, name="validate", help="Validate contract YAML files")
app.add_typer(trigger.app, name="trigger", help="Trigger Databricks jobs")


@app.callback()
def main_callback() -> None:
    """
    Databricks Data Contracts CLI.

    A tool for managing and applying data contracts to Unity Catalog.

    Example:
        $ databricks-contracts apply contract orders_v1 --env prod
        $ databricks-contracts validate contract orders_v1
        $ databricks-contracts validate all
        $ databricks-contracts trigger modified --base-ref origin/main
        $ databricks-contracts publish contract orders_v1 --env prod
    """
    pass


# Version command
@app.command("version")
def version() -> None:
    """
    Show version information.

    Example:
        $ databricks-contracts version
        databricks-contracts 0.1.0
    """
    from databricks_contracts import __version__

    typer.echo(f"databricks-contracts {__version__}")


if __name__ == "__main__":
    app()
