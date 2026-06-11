"""Unit tests for ALTER TABLE statement models."""

from databricks_contracts.models.statements.alter_table import (
    AddColumnsStatement,
    AlterColumnCommentStatement,
    AlterColumnNullabilityStatement,
    AlterTableCommentStatement,
    AlterTablePropertiesStatement,
)


class TestAddColumnsStatement:
    """Tests for AddColumnsStatement DDL generation."""

    def test_basic_nullable_column(self) -> None:
        stmt = AddColumnsStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            column_name="email",
            column_type="STRING",
            nullable=True,
        )
        assert stmt.statement == "ALTER TABLE `cat`.`sch`.`tbl` ADD COLUMNS (  `email` STRING);"

    def test_not_null_column(self) -> None:
        stmt = AddColumnsStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            column_name="id",
            column_type="BIGINT",
            nullable=False,
        )
        assert "NOT NULL" in stmt.statement

    def test_column_with_comment(self) -> None:
        stmt = AddColumnsStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            column_name="age",
            column_type="INT",
            comment="Customer age",
        )
        assert "COMMENT 'Customer age'" in stmt.statement

    def test_column_with_comment_escaping(self) -> None:
        stmt = AddColumnsStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            column_name="note",
            column_type="STRING",
            comment="it's a note",
        )
        assert "COMMENT 'it''s a note'" in stmt.statement

    def test_log_message(self) -> None:
        stmt = AddColumnsStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            column_name="email",
            column_type="STRING",
        )
        assert "email" in stmt.log_message
        assert "`cat`.`sch`.`tbl`" in stmt.log_message


class TestAlterColumnCommentStatement:
    """Tests for AlterColumnCommentStatement DDL generation."""

    def test_basic_comment(self) -> None:
        stmt = AlterColumnCommentStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            column_name="name",
            comment="Full name",
        )
        expected = "ALTER TABLE `cat`.`sch`.`tbl` ALTER COLUMN `name` COMMENT 'Full name';"
        assert stmt.statement == expected

    def test_comment_with_quotes(self) -> None:
        stmt = AlterColumnCommentStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            column_name="desc",
            comment="it's important",
        )
        assert "it''s important" in stmt.statement


class TestAlterColumnNullabilityStatement:
    """Tests for AlterColumnNullabilityStatement DDL generation."""

    def test_set_not_null(self) -> None:
        stmt = AlterColumnNullabilityStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            column_name="id",
            set_not_null=True,
        )
        expected = "ALTER TABLE `cat`.`sch`.`tbl` ALTER COLUMN `id` SET NOT NULL;"
        assert stmt.statement == expected

    def test_drop_not_null(self) -> None:
        stmt = AlterColumnNullabilityStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            column_name="id",
            set_not_null=False,
        )
        expected = "ALTER TABLE `cat`.`sch`.`tbl` ALTER COLUMN `id` DROP NOT NULL;"
        assert stmt.statement == expected


class TestAlterTableCommentStatement:
    """Tests for AlterTableCommentStatement DDL generation."""

    def test_basic_comment(self) -> None:
        stmt = AlterTableCommentStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            comment="Updated description",
        )
        expected = "COMMENT ON TABLE `cat`.`sch`.`tbl` IS 'Updated description';"
        assert stmt.statement == expected


class TestAlterTablePropertiesStatement:
    """Tests for AlterTablePropertiesStatement DDL generation."""

    def test_single_property(self) -> None:
        stmt = AlterTablePropertiesStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            properties={"retention_days": "90"},
        )
        expected = "ALTER TABLE `cat`.`sch`.`tbl` SET TBLPROPERTIES ('retention_days' = '90');"
        assert stmt.statement == expected

    def test_multiple_properties(self) -> None:
        stmt = AlterTablePropertiesStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            properties={
                "refresh_frequency": "daily",
                "retention_days": "90",
            },
        )
        assert "SET TBLPROPERTIES" in stmt.statement
        assert "'refresh_frequency' = 'daily'" in stmt.statement
        assert "'retention_days' = '90'" in stmt.statement

    def test_log_message_lists_keys(self) -> None:
        stmt = AlterTablePropertiesStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            properties={"refresh_frequency": "daily", "retention_days": "90"},
        )
        assert "refresh_frequency" in stmt.log_message
        assert "retention_days" in stmt.log_message
