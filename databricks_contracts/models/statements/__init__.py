"""
DDL statement models.

Models representing SQL DDL statements for Unity Catalog operations.

Example:
    >>> from databricks_contracts.models.statements import CreateTableStatement
    >>> stmt = CreateTableStatement(full_table_name="cat.sch.tbl", ddl="CREATE...")
"""

from databricks_contracts.models.statements.alter_table import (
    AddColumnsStatement,
    AlterColumnCommentStatement,
    AlterColumnNullabilityStatement,
    AlterTableCommentStatement,
    AlterTablePropertiesStatement,
)
from databricks_contracts.models.statements.base import BaseStatement
from databricks_contracts.models.statements.constraint import AddConstraintStatement, DropConstraintStatement
from databricks_contracts.models.statements.create_table import CreateTableStatement
from databricks_contracts.models.statements.grant import GrantStatement
from databricks_contracts.models.statements.tag import TagStatement

__all__ = [
    "BaseStatement",
    "CreateTableStatement",
    "GrantStatement",
    "TagStatement",
    "AddColumnsStatement",
    "AlterColumnCommentStatement",
    "AlterColumnNullabilityStatement",
    "AlterTableCommentStatement",
    "AlterTablePropertiesStatement",
    "AddConstraintStatement",
    "DropConstraintStatement",
]
