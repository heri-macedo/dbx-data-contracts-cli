"""Unit tests for RunResult model."""

from databricks_contracts.models.results.run_result import RunResult


class TestRunResultStatementsCount:
    """Tests for statements_count property."""

    def test_creation_count_with_tags(self) -> None:
        result = RunResult(
            contract_name="test",
            success=True,
            create_ddl="CREATE TABLE...",
            tags_ddl="ALTER TABLE t SET TAGS ('a'='1');\nALTER TABLE t SET TAGS ('b'='2');",
        )
        assert result.statements_count == 3  # 1 CREATE + 2 TAGS

    def test_creation_count_no_tags(self) -> None:
        result = RunResult(contract_name="test", success=True, create_ddl="CREATE TABLE...")
        assert result.statements_count == 1

    def test_evolution_count(self) -> None:
        result = RunResult(
            contract_name="test",
            success=True,
            alter_ddl=["ALTER TABLE t ADD COLUMNS...", "COMMENT ON TABLE t IS..."],
            tags_ddl="ALTER TABLE t SET TAGS ('a'='1');",
            is_evolution=True,
        )
        assert result.statements_count == 3  # 2 ALTERs + 1 TAG

    def test_evolution_count_no_tags(self) -> None:
        result = RunResult(
            contract_name="test",
            success=True,
            alter_ddl=["ALTER TABLE t ADD COLUMNS..."],
            is_evolution=True,
        )
        assert result.statements_count == 1

    def test_failed_result_has_error(self) -> None:
        result = RunResult(
            contract_name="test",
            success=False,
            error="Access denied",
        )
        assert result.error == "Access denied"
        assert result.success is False
