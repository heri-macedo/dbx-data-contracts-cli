"""SQL utility functions shared across the codebase."""


def escape_sql_literal(value: str) -> str:
    """Escape single quotes and normalize newlines for SQL string literals.

    Spark SQL / Databricks SQL string literals are single-quoted.
    The most portable escape for a single quote is doubling it: ' -> ''.
    Newlines are normalized to spaces to avoid multi-line SQL.
    """
    return value.replace("'", "''").replace("\n", " ")
