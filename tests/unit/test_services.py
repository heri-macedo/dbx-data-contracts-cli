"""
Unit tests for services.

Tests for business logic services.

Example:
    $ pytest tests/unit/test_services.py -v
"""

from pathlib import Path

from databricks_contracts.models.contracts import Contract
from databricks_contracts.services.contracts.builder import BuilderService
from databricks_contracts.services.git import ChangeDetectorService
from tests.mocks import MockGitAdapter


class TestChangeDetectorService:
    """Tests for ChangeDetectorService."""

    def test_get_modified_contracts_filters_yaml(self) -> None:
        """
        Test that only .yaml files in contracts path are returned.

        Example:
            >>> detector = ChangeDetectorService(mock_adapter, path)
            >>> contracts = detector.get_modified_contracts()
            >>> assert "orders" in contracts
        """
        # Arrange
        mock_adapter = MockGitAdapter(
            [
                "data_contracts/assets/orders.yaml",
                "data_contracts/assets/customers.yaml",
                "README.md",
                "src/main.py",
            ]
        )
        detector = ChangeDetectorService(
            git_adapter=mock_adapter,
            contracts_path=Path("data_contracts/assets"),
        )

        # Act
        contracts = detector.get_modified_contracts()

        # Assert
        assert len(contracts) == 2
        assert "orders" in contracts
        assert "customers" in contracts

    def test_get_modified_contracts_empty(self) -> None:
        """
        Test with no modified files.

        Example:
            >>> detector = ChangeDetectorService(MockGitAdapter([]), path)
            >>> contracts = detector.get_modified_contracts()
            >>> assert contracts == []
        """
        mock_adapter = MockGitAdapter([])
        detector = ChangeDetectorService(
            git_adapter=mock_adapter,
            contracts_path=Path("data_contracts/assets"),
        )

        contracts = detector.get_modified_contracts()

        assert contracts == []

    def test_get_modified_contracts_ignores_other_yaml(self) -> None:
        """
        Test that YAML files outside contracts path are ignored.

        Example:
            >>> detector = ChangeDetectorService(mock_adapter, path)
            >>> contracts = detector.get_modified_contracts()
            >>> assert "config" not in contracts
        """
        mock_adapter = MockGitAdapter(
            [
                "data_contracts/assets/orders.yaml",
                "config/settings.yaml",
                "docs/readme.yaml",
            ]
        )
        detector = ChangeDetectorService(
            git_adapter=mock_adapter,
            contracts_path=Path("data_contracts/assets"),
        )

        contracts = detector.get_modified_contracts()

        assert len(contracts) == 1
        assert "orders" in contracts


class TestBuilderService:
    def test_build_escapes_single_quotes_in_comments(self) -> None:
        """
        Ensure single quotes are escaped portably for SQL literals (''), not backslash-escaped.
        """
        # Minimal project config (avoid file IO)
        project_config_data = {
            "domain": {"name": "test_catalog", "sub_domain": "test_schema", "description": "Test Domain"},
            "environments": {"dev": {"catalog_suffix": ""}, "prod": {"catalog_suffix": "_prod"}},
        }

        # Minimal contract data
        contract_data = {
            "contract": {"name": "problem_quote_break_v1", "version": "1.0.0", "status": "active"},
            "catalog": "test_catalog",
            "schema": "test_schema",
            "ownership": {
                "data_owner": "Data Owner",
                "bds": "BDS",
                "tds": "TDS",
                "purview_collection": "TestCollection",
                "portfolio": "Portfolio_1",
                "sub_domain": "Sub_Domain_1",
                "business_description": "Test contract description.",
            },
            "table": {
                "name": "problem_quote_break",
                "description": "Snapshot of customer's order\n(daily snapshot)",
                "refresh_frequency": "daily",
                "retention_days": 30,
                "tags": {"layer": "Bronze", "classification": "Classification_1"},
                "columns": [
                    {
                        "name": "order_id",
                        "type": "string",
                        "description": "Order ID in customer's system",
                        "nullable": False,
                    }
                ],
            },
        }

        from databricks_contracts.config.project_config_model import ProjectConfig

        contract = Contract.model_validate(contract_data)
        project_config = ProjectConfig.model_validate(project_config_data)

        builder = BuilderService(environment="dev", project_config=project_config)
        build_result = builder.build(contract)
        ddl = build_result.create_ddl

        assert "customer''s" in ddl
        assert "\\'" not in ddl
