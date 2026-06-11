"""Unit tests for ValidateHandler."""

from pathlib import Path

import pytest
import yaml

from databricks_contracts.handlers.validate_handler import ValidateHandler
from databricks_contracts.models.inputs.validate_input import ValidateInput
from databricks_contracts.services.contracts.loader import ContractLoaderService


@pytest.fixture
def contracts_dir(tmp_path: Path, sample_contract_data: dict) -> Path:
    """Create a temp contracts directory with a valid YAML file."""
    contracts = tmp_path / "contracts"
    contracts.mkdir()
    with open(contracts / "valid_contract.yaml", "w") as f:
        yaml.dump(sample_contract_data, f)
    return contracts


@pytest.fixture
def loader_with_contracts(contracts_dir: Path) -> ContractLoaderService:
    return ContractLoaderService(contracts_path=contracts_dir)


class TestValidateHandlerSingle:
    """Tests for single contract validation."""

    def test_valid_contract(self, loader_with_contracts: ContractLoaderService) -> None:
        handler = ValidateHandler(loader_with_contracts)
        result = handler.handle(ValidateInput(contract_name="valid_contract"))
        assert result.valid is True
        assert result.contract_name == "valid_contract"

    def test_invalid_contract(self, tmp_path: Path) -> None:
        contracts = tmp_path / "contracts"
        contracts.mkdir()
        with open(contracts / "bad_contract.yaml", "w") as f:
            yaml.dump({"contract": {"name": "x"}}, f)

        loader = ContractLoaderService(contracts_path=contracts)
        handler = ValidateHandler(loader)
        result = handler.handle(ValidateInput(contract_name="bad_contract"))
        assert result.valid is False
        assert result.error_count > 0

    def test_missing_contract(self, tmp_path: Path) -> None:
        contracts = tmp_path / "contracts"
        contracts.mkdir()

        loader = ContractLoaderService(contracts_path=contracts)
        handler = ValidateHandler(loader)
        result = handler.handle(ValidateInput(contract_name="nonexistent"))
        assert result.valid is False
        assert "not found" in result.error.lower()


class TestValidateHandlerAll:
    """Tests for validating all contracts."""

    def test_validate_all(self, loader_with_contracts: ContractLoaderService) -> None:
        handler = ValidateHandler(loader_with_contracts)
        results = handler.handle(ValidateInput())
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0].valid is True

    def test_validate_all_empty_directory(self, tmp_path: Path) -> None:
        contracts = tmp_path / "contracts"
        contracts.mkdir()

        loader = ContractLoaderService(contracts_path=contracts)
        handler = ValidateHandler(loader)
        results = handler.handle(ValidateInput())
        assert isinstance(results, list)
        assert len(results) == 0

    def test_validate_all_mixed(self, tmp_path: Path, sample_contract_data: dict) -> None:
        contracts = tmp_path / "contracts"
        contracts.mkdir()

        # Valid contract
        with open(contracts / "good.yaml", "w") as f:
            yaml.dump(sample_contract_data, f)

        # Invalid contract
        with open(contracts / "bad.yaml", "w") as f:
            yaml.dump({"contract": {"name": "x"}}, f)

        loader = ContractLoaderService(contracts_path=contracts)
        handler = ValidateHandler(loader)
        results = handler.handle(ValidateInput())
        assert isinstance(results, list)
        assert len(results) == 2
        valid = [r for r in results if r.valid]
        invalid = [r for r in results if not r.valid]
        assert len(valid) == 1
        assert len(invalid) == 1
