"""Unit tests for StatementBuildResult and EvolutionBuildResult."""

import pytest

from databricks_contracts.models.results.build_result import EvolutionBuildResult, StatementBuildResult
from databricks_contracts.models.statements.alter_table import AlterTableCommentStatement
from databricks_contracts.models.statements.create_table import CreateTableStatement
from databricks_contracts.models.statements.grant import GrantStatement
from databricks_contracts.models.statements.tag import TagStatement


@pytest.fixture
def create_stmt() -> CreateTableStatement:
    return CreateTableStatement(
        full_table_name="`cat`.`sch`.`tbl`",
        ddl="CREATE TABLE IF NOT EXISTS `cat`.`sch`.`tbl` (`id` STRING);",
    )


@pytest.fixture
def tag_stmt() -> TagStatement:
    return TagStatement(
        target="table",
        tags={"layer": "Gold"},
        full_table_name="`cat`.`sch`.`tbl`",
    )


@pytest.fixture
def grant_stmt() -> GrantStatement:
    return GrantStatement(
        full_table_name="`cat`.`sch`.`tbl`",
        principal="test-sp",
    )


class TestStatementBuildResult:
    """Tests for StatementBuildResult."""

    def test_all_statements_with_grant(
        self, create_stmt: CreateTableStatement, tag_stmt: TagStatement, grant_stmt: GrantStatement
    ) -> None:
        result = StatementBuildResult(create_table=create_stmt, tags=[tag_stmt], grant=grant_stmt)
        assert len(result.all_statements) == 3

    def test_all_statements_without_grant(self, create_stmt: CreateTableStatement, tag_stmt: TagStatement) -> None:
        result = StatementBuildResult(create_table=create_stmt, tags=[tag_stmt], grant=None)
        stmts = result.all_statements
        assert len(stmts) == 2
        assert all(s is not None for s in stmts)

    def test_create_ddl(self, create_stmt: CreateTableStatement) -> None:
        result = StatementBuildResult(create_table=create_stmt)
        assert "CREATE TABLE" in result.create_ddl

    def test_tags_ddl(self, create_stmt: CreateTableStatement, tag_stmt: TagStatement) -> None:
        result = StatementBuildResult(create_table=create_stmt, tags=[tag_stmt])
        assert "SET TAGS" in result.tags_ddl


class TestEvolutionBuildResult:
    """Tests for EvolutionBuildResult."""

    def test_has_changes_with_alter(self) -> None:
        alter = AlterTableCommentStatement(full_table_name="`cat`.`sch`.`tbl`", comment="New")
        result = EvolutionBuildResult(alter_statements=[alter])
        assert result.has_changes is True

    def test_has_changes_with_tags_only(self, tag_stmt: TagStatement) -> None:
        result = EvolutionBuildResult(tag_statements=[tag_stmt])
        assert result.has_changes is True

    def test_no_changes(self) -> None:
        result = EvolutionBuildResult()
        assert result.has_changes is False

    def test_all_statements_order(self, tag_stmt: TagStatement, grant_stmt: GrantStatement) -> None:
        alter = AlterTableCommentStatement(full_table_name="`cat`.`sch`.`tbl`", comment="New")
        result = EvolutionBuildResult(
            alter_statements=[alter],
            tag_statements=[tag_stmt],
            grant=grant_stmt,
        )
        stmts = result.all_statements
        assert len(stmts) == 3

    def test_warnings(self) -> None:
        result = EvolutionBuildResult(warnings=["Column old_col skipped"])
        assert len(result.warnings) == 1
