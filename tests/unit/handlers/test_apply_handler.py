"""Unit tests for ApplyHandler — creation and evolution flows."""

from unittest.mock import MagicMock

import pytest

from databricks_contracts.handlers.apply_handler import ApplyHandler
from databricks_contracts.models.contracts.contract import Contract
from databricks_contracts.models.inputs.apply_input import ApplyInput
from databricks_contracts.models.results.execution_result import ExecutionResult
from databricks_contracts.services.contracts.builder import BuilderService
from databricks_contracts.services.contracts.schema_differ import DiffType, SchemaDiff, SchemaDifferService
from databricks_contracts.services.databricks.table_inspector import (
    ExistingColumn,
    ExistingTableSchema,
    TableInspectorService,
)


@pytest.fixture
def contract(sample_contract_data: dict) -> Contract:
    return Contract.model_validate(sample_contract_data)


@pytest.fixture
def mock_loader(contract: Contract) -> MagicMock:
    loader = MagicMock()
    loader.load.return_value = contract
    return loader


@pytest.fixture
def mock_executor() -> MagicMock:
    executor = MagicMock()
    executor.execute.return_value = ExecutionResult(statement="test", success=True)
    return executor


@pytest.fixture
def mock_inspector_new_table() -> MagicMock:
    inspector = MagicMock(spec=TableInspectorService)
    inspector.inspect.return_value = ExistingTableSchema(exists=False)
    return inspector


@pytest.fixture
def mock_inspector_existing_table() -> MagicMock:
    inspector = MagicMock(spec=TableInspectorService)
    inspector.inspect.return_value = ExistingTableSchema(
        exists=True,
        columns=[
            ExistingColumn(name="id", type="STRING", nullable=False, comment="Primary key"),
            ExistingColumn(name="name", type="STRING", nullable=True, comment="Name field"),
        ],
        comment="Test table description",
        tblproperties={
            "refresh_frequency": "daily",
            "retention_days": "90",
            "delta.deletedFileRetentionDuration": "interval 90 days",
            "delta.logRetentionDuration": "interval 90 days",
        },
    )
    return inspector


@pytest.fixture
def mock_differ_no_changes() -> MagicMock:
    differ = MagicMock(spec=SchemaDifferService)
    differ.diff.return_value = []
    return differ


class TestApplyHandlerCreation:
    """Tests for the table creation flow (table does not exist)."""

    def test_creates_table_successfully(
        self,
        mock_loader: MagicMock,
        mock_executor: MagicMock,
        mock_inspector_new_table: MagicMock,
        mock_differ_no_changes: MagicMock,
        sample_project_config_data: dict,
    ) -> None:
        from databricks_contracts.config.project_config_model import ProjectConfig

        config = ProjectConfig.model_validate(sample_project_config_data)
        builder = BuilderService(environment="dev", project_config=config)

        handler = ApplyHandler(mock_loader, builder, mock_executor, mock_inspector_new_table, mock_differ_no_changes)
        result = handler.handle(ApplyInput(contract_name="test_contract"))

        assert result.success is True
        assert result.is_evolution is False
        assert "CREATE TABLE" in result.create_ddl

    def test_creation_failure_returns_error(
        self,
        mock_loader: MagicMock,
        mock_inspector_new_table: MagicMock,
        mock_differ_no_changes: MagicMock,
        sample_project_config_data: dict,
    ) -> None:
        from databricks_contracts.config.project_config_model import ProjectConfig

        config = ProjectConfig.model_validate(sample_project_config_data)
        builder = BuilderService(environment="dev", project_config=config)

        executor = MagicMock()
        executor.execute.return_value = ExecutionResult(
            statement="CREATE TABLE...", success=False, error="Access denied"
        )

        handler = ApplyHandler(mock_loader, builder, executor, mock_inspector_new_table, mock_differ_no_changes)
        result = handler.handle(ApplyInput(contract_name="test_contract"))

        assert result.success is False
        assert result.error == "Access denied"


class TestApplyHandlerEvolution:
    """Tests for the schema evolution flow (table already exists)."""

    def test_evolution_no_changes(
        self,
        mock_loader: MagicMock,
        mock_executor: MagicMock,
        mock_inspector_existing_table: MagicMock,
        mock_differ_no_changes: MagicMock,
        sample_project_config_data: dict,
    ) -> None:
        from databricks_contracts.config.project_config_model import ProjectConfig

        config = ProjectConfig.model_validate(sample_project_config_data)
        builder = BuilderService(environment="dev", project_config=config)

        handler = ApplyHandler(
            mock_loader, builder, mock_executor, mock_inspector_existing_table, mock_differ_no_changes
        )
        result = handler.handle(ApplyInput(contract_name="test_contract"))

        assert result.success is True
        assert result.is_evolution is True

    def test_evolution_with_add_column(
        self,
        mock_loader: MagicMock,
        mock_executor: MagicMock,
        mock_inspector_existing_table: MagicMock,
        sample_project_config_data: dict,
        sample_contract_data: dict,
    ) -> None:
        from databricks_contracts.config.project_config_model import ProjectConfig

        # Add a new column to the contract
        sample_contract_data["table"]["columns"].append(
            {"name": "email", "type": "STRING", "description": "Email", "nullable": True}
        )
        contract = Contract.model_validate(sample_contract_data)
        mock_loader.load.return_value = contract

        config = ProjectConfig.model_validate(sample_project_config_data)
        builder = BuilderService(environment="dev", project_config=config)

        differ = MagicMock(spec=SchemaDifferService)
        differ.diff.return_value = [
            SchemaDiff(diff_type=DiffType.ADD_COLUMN, column_name="email", desired_value="STRING"),
        ]

        handler = ApplyHandler(mock_loader, builder, mock_executor, mock_inspector_existing_table, differ)
        result = handler.handle(ApplyInput(contract_name="test_contract"))

        assert result.success is True
        assert result.is_evolution is True
        assert len(result.alter_ddl) == 1
        assert "ADD COLUMNS" in result.alter_ddl[0]

    def test_evolution_with_warnings(
        self,
        mock_loader: MagicMock,
        mock_executor: MagicMock,
        mock_inspector_existing_table: MagicMock,
        sample_project_config_data: dict,
    ) -> None:
        from databricks_contracts.config.project_config_model import ProjectConfig

        config = ProjectConfig.model_validate(sample_project_config_data)
        builder = BuilderService(environment="dev", project_config=config)

        differ = MagicMock(spec=SchemaDifferService)
        differ.diff.return_value = [
            SchemaDiff(
                diff_type=DiffType.REMOVE_COLUMN,
                column_name="old_col",
                current_value="STRING",
                is_safe=False,
            ),
        ]

        handler = ApplyHandler(mock_loader, builder, mock_executor, mock_inspector_existing_table, differ)
        result = handler.handle(ApplyInput(contract_name="test_contract"))

        assert result.success is True
        assert len(result.warnings) >= 1
        assert any("old_col" in w for w in result.warnings)

    def test_evolution_alter_failure_returns_error(
        self,
        mock_loader: MagicMock,
        mock_inspector_existing_table: MagicMock,
        sample_project_config_data: dict,
    ) -> None:
        from databricks_contracts.config.project_config_model import ProjectConfig

        config = ProjectConfig.model_validate(sample_project_config_data)
        builder = BuilderService(environment="dev", project_config=config)

        executor = MagicMock()
        executor.execute.return_value = ExecutionResult(statement="ALTER TABLE...", success=False, error="ALTER failed")

        differ = MagicMock(spec=SchemaDifferService)
        differ.diff.return_value = [
            SchemaDiff(diff_type=DiffType.UPDATE_TABLE_COMMENT, desired_value="New comment"),
        ]

        handler = ApplyHandler(mock_loader, builder, executor, mock_inspector_existing_table, differ)
        result = handler.handle(ApplyInput(contract_name="test_contract"))

        assert result.success is False
        assert result.error == "ALTER failed"
