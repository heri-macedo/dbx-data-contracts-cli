"""Unit tests for GrantStatement."""

from databricks_contracts.models.statements.grant import GrantStatement


class TestGrantStatement:
    def test_statement(self) -> None:
        stmt = GrantStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            principal="sp-id-123",
        )
        assert "GRANT MODIFY" in stmt.statement
        assert "`cat`.`sch`.`tbl`" in stmt.statement
        assert "`sp-id-123`" in stmt.statement

    def test_log_message(self) -> None:
        stmt = GrantStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            principal="sp-id-123",
        )
        assert "sp-id-123" in stmt.log_message
        assert "`cat`.`sch`.`tbl`" in stmt.log_message
