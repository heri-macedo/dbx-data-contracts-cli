"""ALTER TABLE statement models for schema evolution."""

from typing import Optional

from pydantic import Field

from databricks_contracts.config.constants import DDLKeywords
from databricks_contracts.models.statements.base import BaseStatement
from databricks_contracts.utils.sql import escape_sql_literal


class AddColumnsStatement(BaseStatement):
    """ALTER TABLE t ADD COLUMNS (col TYPE [NOT NULL] COMMENT '...')."""

    full_table_name: str = Field(..., description="Fully qualified table name with backticks")
    column_name: str = Field(..., description="Column name to add")
    column_type: str = Field(..., description="Column data type")
    nullable: bool = Field(default=True, description="Whether column accepts NULL")
    comment: Optional[str] = Field(default=None, description="Column comment")

    @property
    def statement(self) -> str:
        parts = [f"  `{self.column_name}` {self.column_type}"]
        if not self.nullable:
            parts.append(DDLKeywords.NOT_NULL)
        if self.comment:
            escaped = escape_sql_literal(self.comment)
            parts.append(f"{DDLKeywords.COMMENT} '{escaped}'")
        col_def = " ".join(parts)
        return f"{DDLKeywords.ALTER_TABLE} {self.full_table_name} {DDLKeywords.ADD_COLUMNS} ({col_def});"

    @property
    def log_message(self) -> str:
        return f"Adding column `{self.column_name}` to {self.full_table_name}"


class AlterColumnCommentStatement(BaseStatement):
    """ALTER TABLE t ALTER COLUMN c COMMENT '...'."""

    full_table_name: str = Field(..., description="Fully qualified table name with backticks")
    column_name: str = Field(..., description="Column name")
    comment: str = Field(..., description="New column comment")

    @property
    def statement(self) -> str:
        escaped = escape_sql_literal(self.comment)
        return (
            f"{DDLKeywords.ALTER_TABLE} {self.full_table_name} "
            f"{DDLKeywords.ALTER_COLUMN} `{self.column_name}` "
            f"{DDLKeywords.COMMENT} '{escaped}';"
        )

    @property
    def log_message(self) -> str:
        return f"Updating comment on column `{self.column_name}` in {self.full_table_name}"


class AlterColumnNullabilityStatement(BaseStatement):
    """ALTER TABLE t ALTER COLUMN c SET NOT NULL / DROP NOT NULL."""

    full_table_name: str = Field(..., description="Fully qualified table name with backticks")
    column_name: str = Field(..., description="Column name")
    set_not_null: bool = Field(..., description="True = SET NOT NULL, False = DROP NOT NULL")

    @property
    def statement(self) -> str:
        action = DDLKeywords.SET_NOT_NULL if self.set_not_null else DDLKeywords.DROP_NOT_NULL
        return (
            f"{DDLKeywords.ALTER_TABLE} {self.full_table_name} "
            f"{DDLKeywords.ALTER_COLUMN} `{self.column_name}` "
            f"{action};"
        )

    @property
    def log_message(self) -> str:
        action = "SET NOT NULL" if self.set_not_null else "DROP NOT NULL"
        return f"{action} on column `{self.column_name}` in {self.full_table_name}"


class AlterTableCommentStatement(BaseStatement):
    """COMMENT ON TABLE t IS '...'."""

    full_table_name: str = Field(..., description="Fully qualified table name with backticks")
    comment: str = Field(..., description="New table comment")

    @property
    def statement(self) -> str:
        escaped = escape_sql_literal(self.comment)
        return f"{DDLKeywords.COMMENT_ON_TABLE} {self.full_table_name} IS '{escaped}';"

    @property
    def log_message(self) -> str:
        return f"Updating comment on {self.full_table_name}"


class AlterTablePropertiesStatement(BaseStatement):
    """ALTER TABLE t SET TBLPROPERTIES (...)."""

    full_table_name: str = Field(..., description="Fully qualified table name with backticks")
    properties: dict[str, str] = Field(..., description="Properties to set")

    @property
    def statement(self) -> str:
        props_sql = ", ".join(f"'{k}' = '{escape_sql_literal(v)}'" for k, v in self.properties.items())
        return f"{DDLKeywords.ALTER_TABLE} {self.full_table_name} {DDLKeywords.SET_TBLPROPERTIES} ({props_sql});"

    @property
    def log_message(self) -> str:
        keys = ", ".join(self.properties.keys())
        return f"Updating TBLPROPERTIES ({keys}) on {self.full_table_name}"
