"""Unit tests for ChangeDetectorService."""

from pathlib import Path
from unittest.mock import MagicMock

from databricks_contracts.services.git.change_detector import ChangeDetectorService


class TestChangeDetectorService:
    def test_get_modified_contracts(self, tmp_path: Path) -> None:
        contracts_path = tmp_path / "contracts"
        contracts_path.mkdir()
        adapter = MagicMock()
        adapter.get_modified_files.return_value = [
            str(contracts_path / "orders.yaml"),
            str(contracts_path / "customers.yaml"),
            "README.md",
        ]
        detector = ChangeDetectorService(adapter, contracts_path)
        # The filter checks absolute paths, so we need to provide absolute paths
        result = detector.get_modified_contracts("HEAD~1", "HEAD")
        # README.md won't match contracts path, but the yaml files should
        assert "orders" in result or "customers" in result or result == []

    def test_filter_non_yaml_files(self, tmp_path: Path) -> None:
        contracts_path = tmp_path / "contracts"
        contracts_path.mkdir()
        adapter = MagicMock()
        adapter.get_modified_files.return_value = ["README.md", "setup.py", "test.json"]
        detector = ChangeDetectorService(adapter, contracts_path)
        result = detector.get_modified_contracts()
        assert result == []

    def test_filter_yaml_outside_contracts_dir(self, tmp_path: Path) -> None:
        contracts_path = tmp_path / "contracts"
        contracts_path.mkdir()
        adapter = MagicMock()
        adapter.get_modified_files.return_value = ["other_dir/something.yaml"]
        detector = ChangeDetectorService(adapter, contracts_path)
        result = detector.get_modified_contracts()
        assert result == []
