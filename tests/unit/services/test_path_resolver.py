"""Unit tests for PathResolverService."""

import pytest

from databricks_contracts.services.paths.path_resolver import PathResolverService
from databricks_contracts.services.paths.strategies.local import LocalPathStrategy


class TestPathResolverService:
    """Tests for PathResolverService."""

    def test_create_returns_resolver(self) -> None:
        resolver = PathResolverService.create()
        assert resolver is not None

    def test_with_explicit_strategy(self) -> None:
        strategy = LocalPathStrategy()
        resolver = PathResolverService(strategy=strategy)
        assert resolver.contracts_path is not None
        assert resolver.config_path is not None

    def test_local_detection_without_databricks_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)
        resolver = PathResolverService.create()
        # Should use LocalPathStrategy since we're not in Databricks
        assert resolver.contracts_path is not None

    def test_databricks_detection_with_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATABRICKS_RUNTIME_VERSION", "14.3")
        monkeypatch.setenv("PROJECT_ROOT", "/Workspace/project")
        resolver = PathResolverService.create()
        assert resolver.contracts_path is not None
