"""Unit tests for DropConstraintStatement."""

from databricks_contracts.models.statements.constraint import DropConstraintStatement


class TestDropConstraintStatement:
    def test_statement(self) -> None:
        stmt = DropConstraintStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            constraint_name="chk_tbl_col",
        )
        assert "DROP CONSTRAINT" in stmt.statement
        assert "chk_tbl_col" in stmt.statement

    def test_log_message(self) -> None:
        stmt = DropConstraintStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            constraint_name="chk_tbl_col",
        )
        assert "Dropping constraint" in stmt.log_message
        assert "chk_tbl_col" in stmt.log_message
