"""Unit tests for ApplyHandler warning paths — tag/constraint/grant failures."""

from unittest.mock import MagicMock

from databricks_contracts.config.project_config_model import ProjectConfig
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


def _make_handler(
    sample_contract_data: dict,
    sample_project_config_data: dict,
    executor: MagicMock,
    existing: ExistingTableSchema,
    diffs: list[SchemaDiff] | None = None,
) -> tuple[ApplyHandler, Contract]:
    contract = Contract.model_validate(sample_contract_data)
    loader = MagicMock()
    loader.load.return_value = contract
    config = ProjectConfig.model_validate(sample_project_config_data)
    builder = BuilderService(environment="dev", project_config=config)
    inspector = MagicMock(spec=TableInspectorService)
    inspector.inspect.return_value = existing
    differ = MagicMock(spec=SchemaDifferService)
    differ.diff.return_value = diffs or []
    return ApplyHandler(loader, builder, executor, inspector, differ), contract


class TestApplyHandlerCreationWarnings:
    """Tests for non-fatal warnings during table creation."""

    def test_tag_failure_becomes_warning(self, sample_contract_data: dict, sample_project_config_data: dict) -> None:
        call_count = 0

        def execute_side_effect(stmt: object) -> ExecutionResult:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # CREATE TABLE succeeds
                return ExecutionResult(statement="CREATE...", success=True)
            # Tags fail
            return ExecutionResult(statement="ALTER TAG...", success=False, error="PERMISSION_DENIED")

        executor = MagicMock()
        executor.execute.side_effect = execute_side_effect

        handler, _ = _make_handler(
            sample_contract_data, sample_project_config_data, executor, ExistingTableSchema(exists=False)
        )
        result = handler.handle(ApplyInput(contract_name="test_contract"))

        assert result.success is True
        assert len(result.warnings) > 0

    def test_grant_failure_becomes_warning(self, sample_contract_data: dict, sample_project_config_data: dict) -> None:
        calls = []

        def execute_side_effect(stmt: object) -> ExecutionResult:
            calls.append(stmt)
            # The last call for a creation is the grant (after create + tags + constraints)
            if hasattr(stmt, "principal"):
                return ExecutionResult(statement="GRANT...", success=False, error="GRANT_DENIED")
            return ExecutionResult(statement="OK", success=True)

        executor = MagicMock()
        executor.execute.side_effect = execute_side_effect

        handler, _ = _make_handler(
            sample_contract_data, sample_project_config_data, executor, ExistingTableSchema(exists=False)
        )
        result = handler.handle(ApplyInput(contract_name="test_contract"))

        assert result.success is True
        assert any("GRANT" in w for w in result.warnings)

    def test_constraint_failure_becomes_warning(
        self, sample_contract_data: dict, sample_project_config_data: dict
    ) -> None:
        sample_contract_data["table"]["columns"].append(
            {"name": "age", "type": "INT", "description": "Age", "constraints": {"check": "age > 0"}}
        )

        def execute_side_effect(stmt: object) -> ExecutionResult:
            if hasattr(stmt, "check_expression"):
                return ExecutionResult(statement="ADD CONSTRAINT...", success=False, error="CONSTRAINT_ERROR")
            return ExecutionResult(statement="OK", success=True)

        executor = MagicMock()
        executor.execute.side_effect = execute_side_effect

        handler, _ = _make_handler(
            sample_contract_data, sample_project_config_data, executor, ExistingTableSchema(exists=False)
        )
        result = handler.handle(ApplyInput(contract_name="test_contract"))

        assert result.success is True
        assert any("Constraint" in w or "constraint" in w or "CONSTRAINT" in w for w in result.warnings)

    def test_exception_returns_error_result(self, sample_contract_data: dict, sample_project_config_data: dict) -> None:
        loader = MagicMock()
        loader.load.side_effect = RuntimeError("Unexpected error")
        config = ProjectConfig.model_validate(sample_project_config_data)
        builder = BuilderService(environment="dev", project_config=config)
        executor = MagicMock()
        inspector = MagicMock(spec=TableInspectorService)
        differ = MagicMock(spec=SchemaDifferService)

        handler = ApplyHandler(loader, builder, executor, inspector, differ)
        result = handler.handle(ApplyInput(contract_name="test_contract"))

        assert result.success is False
        assert "Unexpected error" in result.error


class TestApplyHandlerEvolutionWarnings:
    """Tests for non-fatal warnings during schema evolution."""

    def _existing_schema(self) -> ExistingTableSchema:
        return ExistingTableSchema(
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

    def test_evolution_tag_failure_warning(self, sample_contract_data: dict, sample_project_config_data: dict) -> None:
        def execute_side_effect(stmt: object) -> ExecutionResult:
            if hasattr(stmt, "tags"):
                return ExecutionResult(statement="TAG...", success=False, error="TAG_DENIED")
            return ExecutionResult(statement="OK", success=True)

        executor = MagicMock()
        executor.execute.side_effect = execute_side_effect

        handler, _ = _make_handler(sample_contract_data, sample_project_config_data, executor, self._existing_schema())
        result = handler.handle(ApplyInput(contract_name="test_contract"))

        assert result.success is True
        assert result.is_evolution is True
        assert any("TAG_DENIED" in w for w in result.warnings)

    def test_evolution_grant_failure_warning(
        self, sample_contract_data: dict, sample_project_config_data: dict
    ) -> None:
        def execute_side_effect(stmt: object) -> ExecutionResult:
            if hasattr(stmt, "principal"):
                return ExecutionResult(statement="GRANT...", success=False, error="GRANT_ERR")
            return ExecutionResult(statement="OK", success=True)

        executor = MagicMock()
        executor.execute.side_effect = execute_side_effect

        handler, _ = _make_handler(sample_contract_data, sample_project_config_data, executor, self._existing_schema())
        result = handler.handle(ApplyInput(contract_name="test_contract"))

        assert result.success is True
        assert any("GRANT" in w for w in result.warnings)

    def test_evolution_constraint_failure_warning(
        self, sample_contract_data: dict, sample_project_config_data: dict
    ) -> None:
        sample_contract_data["table"]["columns"].append(
            {"name": "age", "type": "INT", "description": "Age", "constraints": {"check": "age > 0"}}
        )

        def execute_side_effect(stmt: object) -> ExecutionResult:
            if hasattr(stmt, "check_expression"):
                return ExecutionResult(statement="ADD CONSTRAINT...", success=False, error="ALREADY_EXISTS")
            return ExecutionResult(statement="OK", success=True)

        executor = MagicMock()
        executor.execute.side_effect = execute_side_effect

        handler, _ = _make_handler(
            sample_contract_data,
            sample_project_config_data,
            executor,
            self._existing_schema(),
            diffs=[SchemaDiff(diff_type=DiffType.ADD_COLUMN, column_name="age", desired_value="INT")],
        )
        result = handler.handle(ApplyInput(contract_name="test_contract"))

        assert result.success is True
        assert any("ALREADY_EXISTS" in w for w in result.warnings)

    def test_evolution_with_warnings_logging(
        self, sample_contract_data: dict, sample_project_config_data: dict
    ) -> None:
        """Test the logging path for successful evolution with warnings."""
        executor = MagicMock()
        executor.execute.return_value = ExecutionResult(statement="OK", success=True)

        handler, _ = _make_handler(
            sample_contract_data,
            sample_project_config_data,
            executor,
            self._existing_schema(),
            diffs=[
                SchemaDiff(
                    diff_type=DiffType.REMOVE_COLUMN,
                    column_name="old",
                    current_value="STRING",
                    is_safe=False,
                )
            ],
        )
        result = handler.handle(ApplyInput(contract_name="test_contract"))

        assert result.success is True
        assert len(result.warnings) >= 1
