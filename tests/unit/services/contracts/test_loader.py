"""Unit tests for ContractLoaderService."""

from pathlib import Path

import pytest
import yaml

from databricks_contracts.exceptions import ContractNotFoundError, ContractParseError
from databricks_contracts.services.contracts.loader import ContractLoaderService


@pytest.fixture
def contracts_dir(tmp_path: Path, sample_contract_data: dict) -> Path:
    contracts = tmp_path / "contracts"
    contracts.mkdir()
    with open(contracts / "test_contract.yaml", "w") as f:
        yaml.dump(sample_contract_data, f)
    return contracts


@pytest.fixture
def loader(contracts_dir: Path) -> ContractLoaderService:
    return ContractLoaderService(contracts_path=contracts_dir)


class TestContractLoaderServiceInit:
    """Tests for initialization."""

    def test_explicit_path(self, contracts_dir: Path) -> None:
        loader = ContractLoaderService(contracts_path=contracts_dir)
        assert loader.contracts_path == contracts_dir

    def test_get_contract_path(self, loader: ContractLoaderService, contracts_dir: Path) -> None:
        path = loader.get_contract_path("my_contract")
        assert path == contracts_dir / "my_contract.yaml"


class TestContractLoaderServiceLoadRaw:
    """Tests for load_raw()."""

    def test_load_raw_success(self, loader: ContractLoaderService) -> None:
        data = loader.load_raw("test_contract")
        assert isinstance(data, dict)
        assert data["table"]["name"] == "test_table"

    def test_load_raw_not_found(self, loader: ContractLoaderService) -> None:
        with pytest.raises(ContractNotFoundError, match="not found"):
            loader.load_raw("nonexistent")

    def test_load_raw_invalid_yaml(self, contracts_dir: Path) -> None:
        with open(contracts_dir / "bad.yaml", "w") as f:
            f.write(":\n  invalid: yaml: {{{\n")

        loader = ContractLoaderService(contracts_path=contracts_dir)
        with pytest.raises(ContractParseError, match="Failed to parse"):
            loader.load_raw("bad")


class TestContractLoaderServiceLoad:
    """Tests for load()."""

    def test_load_success(self, loader: ContractLoaderService) -> None:
        contract = loader.load("test_contract")
        assert contract.name == "test_contract"
        assert contract.table.name == "test_table"

    def test_load_not_found(self, loader: ContractLoaderService) -> None:
        with pytest.raises(ContractNotFoundError):
            loader.load("nonexistent")


class TestContractLoaderServiceList:
    """Tests for list_contracts() and exists()."""

    def test_list_contracts(self, loader: ContractLoaderService) -> None:
        contracts = loader.list_contracts()
        assert contracts == ["test_contract"]

    def test_list_contracts_empty_dir(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        loader = ContractLoaderService(contracts_path=empty_dir)
        assert loader.list_contracts() == []

    def test_list_contracts_nonexistent_dir(self, tmp_path: Path) -> None:
        loader = ContractLoaderService(contracts_path=tmp_path / "nonexistent")
        assert loader.list_contracts() == []

    def test_list_contracts_sorted(self, contracts_dir: Path) -> None:
        with open(contracts_dir / "alpha.yaml", "w") as f:
            yaml.dump({}, f)
        with open(contracts_dir / "beta.yaml", "w") as f:
            yaml.dump({}, f)

        loader = ContractLoaderService(contracts_path=contracts_dir)
        contracts = loader.list_contracts()
        assert contracts == ["alpha", "beta", "test_contract"]

    def test_exists_true(self, loader: ContractLoaderService) -> None:
        assert loader.exists("test_contract") is True

    def test_exists_false(self, loader: ContractLoaderService) -> None:
        assert loader.exists("nonexistent") is False
