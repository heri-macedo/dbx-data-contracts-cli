"""Unit tests for constraint statement models."""

from databricks_contracts.models.statements.constraint import AddConstraintStatement, DropConstraintStatement


class TestAddConstraintStatement:
    """Tests for AddConstraintStatement DDL generation."""

    def test_basic_check_constraint(self) -> None:
        stmt = AddConstraintStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            constraint_name="chk_tbl_age",
            check_expression="age > 0 AND age < 150",
        )
        expected = "ALTER TABLE `cat`.`sch`.`tbl` ADD CONSTRAINT chk_tbl_age CHECK (age > 0 AND age < 150);"
        assert stmt.statement == expected

    def test_log_message(self) -> None:
        stmt = AddConstraintStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            constraint_name="chk_tbl_age",
            check_expression="age > 0",
        )
        assert "chk_tbl_age" in stmt.log_message


class TestDropConstraintStatement:
    """Tests for DropConstraintStatement DDL generation."""

    def test_drop_constraint(self) -> None:
        stmt = DropConstraintStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            constraint_name="chk_tbl_age",
        )
        expected = "ALTER TABLE `cat`.`sch`.`tbl` DROP CONSTRAINT chk_tbl_age;"
        assert stmt.statement == expected
