"""Unit tests for ALTER TABLE statement log_message properties."""

from databricks_contracts.models.statements.alter_table import (
    AlterColumnCommentStatement,
    AlterColumnNullabilityStatement,
    AlterTableCommentStatement,
)


class TestAlterTableLogMessages:
    """Tests for log_message properties of ALTER statements."""

    def test_alter_column_comment_log_message(self) -> None:
        stmt = AlterColumnCommentStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            column_name="name",
            comment="Full name",
        )
        assert stmt.log_message == "Updating comment on column `name` in `cat`.`sch`.`tbl`"

    def test_alter_column_set_not_null_log_message(self) -> None:
        stmt = AlterColumnNullabilityStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            column_name="id",
            set_not_null=True,
        )
        assert stmt.log_message == "SET NOT NULL on column `id` in `cat`.`sch`.`tbl`"

    def test_alter_column_drop_not_null_log_message(self) -> None:
        stmt = AlterColumnNullabilityStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            column_name="id",
            set_not_null=False,
        )
        assert stmt.log_message == "DROP NOT NULL on column `id` in `cat`.`sch`.`tbl`"

    def test_alter_table_comment_log_message(self) -> None:
        stmt = AlterTableCommentStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            comment="New desc",
        )
        assert stmt.log_message == "Updating comment on `cat`.`sch`.`tbl`"
