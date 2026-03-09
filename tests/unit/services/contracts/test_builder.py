"""
Unit tests for BuilderService — DDL generation with multiple partition columns.

Tests cover:
    - PARTITIONED BY clause with multiple columns generates correct DDL

Mirrors: databricks_contracts/services/contracts/builder.py

Example:
    $ pytest tests/unit/services/contracts/test_builder.py -v
"""

from databricks_contracts.config.project_config_model import ProjectConfig
from databricks_contracts.models.contracts.contract import Contract
from databricks_contracts.services.contracts.builder import BuilderService


class TestBuilderServicePartitionedBy:
    """Tests for BuilderService DDL generation with partitioned_by."""

    def test_build_with_multiple_partition_columns(
        self,
        sample_builder_contract_with_multiple_partitions: dict,
        sample_builder_project_config_data: dict,
    ) -> None:
        """
        Test that PARTITIONED BY clause includes all columns when multiple are specified.

        When a table is partitioned by two columns (event_date and region),
        the generated DDL should contain a PARTITIONED BY clause with both
        columns properly backtick-quoted and comma-separated.

        Expected DDL fragment:
            PARTITIONED BY (`event_date`, `region`)

        Args:
            sample_builder_contract_with_multiple_partitions: Contract dict with two
                partition columns from fixture.
            sample_builder_project_config_data: Project config dict from fixture.
        """
        # Arrange
        contract = Contract.model_validate(sample_builder_contract_with_multiple_partitions)
        project_config = ProjectConfig.model_validate(sample_builder_project_config_data)
        builder = BuilderService(environment="dev", project_config=project_config)

        # Act
        build_result = builder.build(contract)
        ddl = build_result.create_ddl

        # Assert
        assert "PARTITIONED BY (`event_date`, `region`)" in ddl
