"""Unit tests for TagStatement model — column-level and log_message coverage."""

from databricks_contracts.models.statements.tag import TagStatement


class TestTagStatementColumnLevel:
    """Tests for column-level tag statement generation."""

    def test_column_level_statement(self) -> None:
        stmt = TagStatement(
            target="email",
            tags={"privacy": "PII_HIDDEN"},
            full_table_name="`cat`.`sch`.`tbl`",
        )
        expected = "ALTER TABLE `cat`.`sch`.`tbl` ALTER COLUMN `email` SET TAGS ('privacy' = 'PII_HIDDEN');"
        assert stmt.statement == expected

    def test_column_level_is_not_table_level(self) -> None:
        stmt = TagStatement(
            target="email",
            tags={"privacy": "PII_HIDDEN"},
            full_table_name="`cat`.`sch`.`tbl`",
        )
        assert stmt.is_table_level is False


class TestTagStatementLogMessage:
    """Tests for log_message property."""

    def test_table_level_log_message(self) -> None:
        stmt = TagStatement(
            target="table",
            tags={"layer": "Gold"},
            full_table_name="`cat`.`sch`.`tbl`",
        )
        assert stmt.log_message == "table (layer=Gold)"

    def test_column_level_log_message(self) -> None:
        stmt = TagStatement(
            target="email",
            tags={"privacy": "PII_HIDDEN"},
            full_table_name="`cat`.`sch`.`tbl`",
        )
        assert stmt.log_message == "email (privacy=PII_HIDDEN)"
