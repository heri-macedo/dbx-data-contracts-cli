"""
Entry point for running as a module.

Allows running the CLI with:
    $ python -m databricks_contracts

Example:
    $ python -m databricks_contracts --help
    $ python -m databricks_contracts apply contract orders
    $ python -m databricks_contracts validate all
"""

from databricks_contracts.commands.main import app

if __name__ == "__main__":
    app()
