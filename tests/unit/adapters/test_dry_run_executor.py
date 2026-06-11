"""Unit tests for DryRunExecutor."""

from databricks_contracts.adapters.databricks.executors.dry_run import DryRunExecutor
from databricks_contracts.models.statements.create_table import CreateTableStatement
from databricks_contracts.models.statements.tag import TagStatement


class TestDryRunExecutor:
    """Tests for DryRunExecutor.execute()."""

    def test_execute_returns_success(self) -> None:
        executor = DryRunExecutor()
        stmt = CreateTableStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            ddl="CREATE TABLE IF NOT EXISTS `cat`.`sch`.`tbl` (`id` STRING);",
        )
        result = executor.execute(stmt)
        assert result.success is True
        assert result.dry_run is True
        assert result.error is None

    def test_execute_multiline_statement(self) -> None:
        executor = DryRunExecutor()
        stmt = CreateTableStatement(
            full_table_name="`cat`.`sch`.`tbl`",
            ddl="CREATE TABLE\n  `cat`.`sch`.`tbl`\n  (`id` STRING);",
        )
        result = executor.execute(stmt)
        assert result.success is True

    def test_execute_tag_statement(self) -> None:
        executor = DryRunExecutor()
        stmt = TagStatement(
            target="table",
            tags={"layer": "Gold"},
            full_table_name="`cat`.`sch`.`tbl`",
        )
        result = executor.execute(stmt)
        assert result.success is True
        assert result.dry_run is True

    def test_execute_batch(self) -> None:
        executor = DryRunExecutor()
        stmts = [
            CreateTableStatement(full_table_name="`c`.`s`.`t`", ddl="CREATE TABLE...;"),
            TagStatement(target="table", tags={"layer": "Gold"}, full_table_name="`c`.`s`.`t`"),
        ]
        results = executor.execute_batch(stmts)
        assert len(results) == 2
        assert all(r.success for r in results)
