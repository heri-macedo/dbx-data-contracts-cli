"""CHECK constraint statement models."""

from pydantic import Field

from databricks_contracts.config.constants import DDLKeywords
from databricks_contracts.models.statements.base import BaseStatement


class AddConstraintStatement(BaseStatement):
    """ALTER TABLE t ADD CONSTRAINT chk_table_col CHECK (expr)."""

    full_table_name: str = Field(..., description="Fully qualified table name with backticks")
    constraint_name: str = Field(..., description="Constraint name (e.g. chk_table_col)")
    check_expression: str = Field(..., description="SQL boolean expression for CHECK")

    @property
    def statement(self) -> str:
        return (
            f"{DDLKeywords.ALTER_TABLE} {self.full_table_name} "
            f"{DDLKeywords.ADD_CONSTRAINT} {self.constraint_name} "
            f"{DDLKeywords.CHECK} ({self.check_expression});"
        )

    @property
    def log_message(self) -> str:
        return f"Adding constraint {self.constraint_name} on {self.full_table_name}"


class DropConstraintStatement(BaseStatement):
    """ALTER TABLE t DROP CONSTRAINT chk_table_col."""

    full_table_name: str = Field(..., description="Fully qualified table name with backticks")
    constraint_name: str = Field(..., description="Constraint name to drop")

    @property
    def statement(self) -> str:
        return f"{DDLKeywords.ALTER_TABLE} {self.full_table_name} {DDLKeywords.DROP_CONSTRAINT} {self.constraint_name};"

    @property
    def log_message(self) -> str:
        return f"Dropping constraint {self.constraint_name} on {self.full_table_name}"
