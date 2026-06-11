"""Comprehensive unit tests for BuilderService — DDL generation.

Tests cover:
    - Base CREATE TABLE DDL structure
    - Column definitions (types, NOT NULL, comments)
    - TBLPROPERTIES including retention enforcement
    - Tag statement generation (table-level and column-level)
    - GRANT generation (with and without WORKFLOW_SP_ID)
    - CHECK constraint generation
    - Schema evolution via build_evolution()
"""

import pytest

from databricks_contracts.config.project_config_model import ProjectConfig
from databricks_contracts.models.contracts.contract import Contract
from databricks_contracts.services.contracts.builder import BuilderService
from databricks_contracts.services.contracts.schema_differ import DiffType, SchemaDiff


@pytest.fixture
def project_config(sample_project_config_data: dict) -> ProjectConfig:
    return ProjectConfig.model_validate(sample_project_config_data)


@pytest.fixture
def builder(project_config: ProjectConfig) -> BuilderService:
    return BuilderService(environment="dev", project_config=project_config)


@pytest.fixture
def contract(sample_contract_data: dict) -> Contract:
    return Contract.model_validate(sample_contract_data)


class TestBuilderServiceCreateTable:
    """Tests for CREATE TABLE DDL generation."""

    def test_create_table_structure(self, builder: BuilderService, contract: Contract) -> None:
        result = builder.build(contract)
        ddl = result.create_ddl

        assert "CREATE TABLE IF NOT EXISTS" in ddl
        assert "`test_catalog`.`test_schema`.`test_table`" in ddl
        assert "USING DELTA" in ddl

    def test_column_definitions(self, builder: BuilderService, contract: Contract) -> None:
        result = builder.build(contract)
        ddl = result.create_ddl

        assert "`id` STRING NOT NULL" in ddl
        assert "`name` STRING" in ddl
        assert "COMMENT 'Primary key'" in ddl

    def test_tblproperties_includes_retention_enforcement(self, builder: BuilderService, contract: Contract) -> None:
        result = builder.build(contract)
        ddl = result.create_ddl

        assert "'refresh_frequency' = 'daily'" in ddl
        assert "'retention_days' = '90'" in ddl
        assert "'delta.deletedFileRetentionDuration' = 'interval 90 days'" in ddl
        assert "'delta.logRetentionDuration' = 'interval 90 days'" in ddl

    def test_table_comment(self, builder: BuilderService, contract: Contract) -> None:
        result = builder.build(contract)
        ddl = result.create_ddl
        assert "COMMENT 'Test table description'" in ddl

    def test_without_partitioned_by(self, builder: BuilderService, contract: Contract) -> None:
        result = builder.build(contract)
        ddl = result.create_ddl
        assert "PARTITIONED BY" not in ddl


class TestBuilderServiceTags:
    """Tests for SET TAGS statement generation."""

    def test_generates_table_level_tags(self, builder: BuilderService, contract: Contract) -> None:
        result = builder.build(contract)
        table_tags = [t for t in result.tags if t.is_table_level]

        tag_keys = set()
        for t in table_tags:
            tag_keys.update(t.tags.keys())

        assert "portfolio" in tag_keys
        assert "sub_domain" in tag_keys
        assert "layer" in tag_keys

    def test_generates_column_level_tags(self, builder: BuilderService, sample_contract_data: dict) -> None:
        sample_contract_data["table"]["columns"][0]["tags"] = {"privacy": "PII_HIDDEN"}
        contract = Contract.model_validate(sample_contract_data)
        result = builder.build(contract)

        col_tags = [t for t in result.tags if not t.is_table_level]
        assert len(col_tags) == 1
        assert col_tags[0].target == "id"
        assert col_tags[0].tags == {"privacy": "PII_HIDDEN"}

    def test_one_tag_per_statement(self, builder: BuilderService, contract: Contract) -> None:
        result = builder.build(contract)
        for tag_stmt in result.tags:
            assert len(tag_stmt.tags) == 1


class TestBuilderServiceGrant:
    """Tests for GRANT statement generation."""

    def test_grant_generated_with_sp_id(self, builder: BuilderService, contract: Contract) -> None:
        """WORKFLOW_SP_ID is set by conftest.py autouse fixture."""
        result = builder.build(contract)
        assert result.grant is not None
        assert "GRANT MODIFY" in result.grant.statement

    def test_grant_none_without_sp_id(
        self, builder: BuilderService, contract: Contract, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("WORKFLOW_SP_ID", raising=False)
        result = builder.build(contract)
        assert result.grant is None

    def test_all_statements_excludes_none_grant(
        self, builder: BuilderService, contract: Contract, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("WORKFLOW_SP_ID", raising=False)
        result = builder.build(contract)
        for stmt in result.all_statements:
            assert stmt is not None


class TestBuilderServiceConstraints:
    """Tests for CHECK constraint generation."""

    def test_no_constraints_by_default(self, builder: BuilderService, contract: Contract) -> None:
        result = builder.build(contract)
        assert result.constraints == []

    def test_generates_check_constraint(self, builder: BuilderService, sample_contract_data: dict) -> None:
        sample_contract_data["table"]["columns"].append(
            {
                "name": "age",
                "type": "INT",
                "description": "Age",
                "constraints": {"check": "age > 0 AND age < 150"},
            }
        )
        contract = Contract.model_validate(sample_contract_data)
        result = builder.build(contract)

        assert len(result.constraints) == 1
        assert result.constraints[0].constraint_name == "chk_test_table_age"
        assert "age > 0 AND age < 150" in result.constraints[0].statement


class TestBuilderServiceEvolution:
    """Tests for build_evolution() method."""

    def test_build_evolution_add_column(self, builder: BuilderService, sample_contract_data: dict) -> None:
        sample_contract_data["table"]["columns"].append(
            {"name": "email", "type": "STRING", "description": "Email", "nullable": True}
        )
        contract = Contract.model_validate(sample_contract_data)
        full_name = "`test_catalog`.`test_schema`.`test_table`"

        diffs = [
            SchemaDiff(diff_type=DiffType.ADD_COLUMN, column_name="email", desired_value="STRING"),
        ]
        result = builder.build_evolution(contract, diffs, full_name)

        assert len(result.alter_statements) == 1
        assert "ADD COLUMNS" in result.alter_statements[0].statement

    def test_build_evolution_unsafe_diffs_become_warnings(self, builder: BuilderService, contract: Contract) -> None:
        full_name = "`test_catalog`.`test_schema`.`test_table`"
        diffs = [
            SchemaDiff(
                diff_type=DiffType.REMOVE_COLUMN,
                column_name="old_col",
                current_value="STRING",
                is_safe=False,
            ),
        ]
        result = builder.build_evolution(contract, diffs, full_name)

        assert len(result.alter_statements) == 0
        assert len(result.warnings) == 1
        assert "old_col" in result.warnings[0]

    def test_build_evolution_update_tblproperties(self, builder: BuilderService, contract: Contract) -> None:
        full_name = "`test_catalog`.`test_schema`.`test_table`"
        diffs = [
            SchemaDiff(diff_type=DiffType.UPDATE_TBLPROPERTIES, current_value="{}", desired_value="{}"),
        ]
        result = builder.build_evolution(contract, diffs, full_name)

        assert len(result.alter_statements) == 1
        stmt = result.alter_statements[0].statement
        assert "SET TBLPROPERTIES" in stmt
        assert "'delta.deletedFileRetentionDuration' = 'interval 90 days'" in stmt

    def test_build_evolution_includes_tags(self, builder: BuilderService, contract: Contract) -> None:
        full_name = "`test_catalog`.`test_schema`.`test_table`"
        result = builder.build_evolution(contract, [], full_name)
        assert len(result.tag_statements) > 0

    def test_build_evolution_has_changes(self, builder: BuilderService, contract: Contract) -> None:
        full_name = "`test_catalog`.`test_schema`.`test_table`"
        diffs = [SchemaDiff(diff_type=DiffType.UPDATE_TABLE_COMMENT, desired_value="New comment")]
        result = builder.build_evolution(contract, diffs, full_name)
        assert result.has_changes is True

    def test_build_evolution_modify_column_comment(self, builder: BuilderService, contract: Contract) -> None:
        full_name = "`test_catalog`.`test_schema`.`test_table`"
        diffs = [
            SchemaDiff(
                diff_type=DiffType.MODIFY_COLUMN_COMMENT,
                column_name="id",
                current_value="Old",
                desired_value="New",
            ),
        ]
        result = builder.build_evolution(contract, diffs, full_name)
        assert len(result.alter_statements) == 1
        assert "ALTER COLUMN `id` COMMENT 'New'" in result.alter_statements[0].statement

    def test_build_evolution_set_not_null(self, builder: BuilderService, contract: Contract) -> None:
        full_name = "`test_catalog`.`test_schema`.`test_table`"
        diffs = [
            SchemaDiff(
                diff_type=DiffType.MODIFY_COLUMN_NULLABILITY,
                column_name="name",
                current_value="nullable",
                desired_value="NOT NULL",
            ),
        ]
        result = builder.build_evolution(contract, diffs, full_name)
        assert len(result.alter_statements) == 1
        assert "SET NOT NULL" in result.alter_statements[0].statement

    def test_build_evolution_drop_not_null(self, builder: BuilderService, contract: Contract) -> None:
        full_name = "`test_catalog`.`test_schema`.`test_table`"
        diffs = [
            SchemaDiff(
                diff_type=DiffType.MODIFY_COLUMN_NULLABILITY,
                column_name="id",
                current_value="NOT NULL",
                desired_value="nullable",
            ),
        ]
        result = builder.build_evolution(contract, diffs, full_name)
        assert len(result.alter_statements) == 1
        assert "DROP NOT NULL" in result.alter_statements[0].statement
