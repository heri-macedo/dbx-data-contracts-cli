"""
Pytest configuration and shared fixtures.

Provides common fixtures for all tests.

Example:
    >>> def test_something(sample_contract_data):
    ...     assert sample_contract_data["table"]["name"] == "test_table"
"""

import pytest

from databricks_contracts.config.settings import clear_settings_cache


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Set up test environment and clear settings cache.

    This fixture runs automatically before each test.
    """
    # Clear cached settings to ensure fresh state
    clear_settings_cache()

    # Set WORKFLOW_SP_ID for tests that generate GRANT statements
    monkeypatch.setenv("WORKFLOW_SP_ID", "test-sp-for-unit-tests")


@pytest.fixture
def sample_contract_data() -> dict:
    """
    Provide sample contract data for testing.

    Returns:
        Dictionary matching the Contract schema.

    Example:
        >>> def test_contract(sample_contract_data):
        ...     contract = Contract.model_validate(sample_contract_data)
        ...     assert contract.name == "test_contract"
    """
    return {
        "contract": {
            "name": "test_contract",
            "version": "1.0.0",
            "status": "active",
        },
        "catalog": "test_catalog",
        "schema": "test_schema",
        "ownership": {
            "data_owner": "test@example.com",
            "bds": "bds@example.com",
            "tds": "tds@example.com",
            "purview_collection": "TestCollection",
            "portfolio": "Portfolio_1",
            "sub_domain": "Sub_Domain_1",
            "business_description": "Test business description",
        },
        "table": {
            "name": "test_table",
            "description": "Test table description",
            "refresh_frequency": "daily",
            "retention_days": 90,
            "tags": {
                "layer": "Gold",
            },
            "columns": [
                {
                    "name": "id",
                    "type": "STRING",
                    "description": "Primary key",
                    "nullable": False,
                },
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Name field",
                    "nullable": True,
                },
            ],
        },
    }


@pytest.fixture
def sample_project_config_data() -> dict:
    """
    Provide sample project config data for testing.

    Returns:
        Dictionary matching the ProjectConfig schema.

    Example:
        >>> def test_config(sample_project_config_data):
        ...     config = ProjectConfig.model_validate(sample_project_config_data)
        ...     assert config.get_catalog("prod") == "test_catalog_prod"
    """
    return {
        "domain": {
            "name": "test_catalog",
            "sub_domain": "test_schema",
            "description": "Test domain",
        },
        "environments": {
            "dev": {"catalog_suffix": ""},
            "prod": {"catalog_suffix": "_prod"},
        },
    }
