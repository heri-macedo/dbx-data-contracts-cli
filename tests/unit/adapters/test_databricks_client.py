"""Unit tests for DatabricksClient adapter with mocked SDK."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from databricks_contracts.adapters.databricks.api_client import DatabricksClient
from databricks_contracts.config.settings import Settings

# -- Helpers ------------------------------------------------------------------


def _make_job(job_id: int, name: str | None) -> SimpleNamespace:
    """Create a fake Databricks job listing entry."""
    settings = SimpleNamespace(name=name) if name else None
    return SimpleNamespace(job_id=job_id, settings=settings)


def _make_run(run_id: int | None) -> SimpleNamespace:
    """Create a fake Databricks run_now response."""
    return SimpleNamespace(run_id=run_id)


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def mock_workspace() -> MagicMock:
    """Pre-configured WorkspaceClient mock."""
    return MagicMock()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, mock_workspace: MagicMock) -> DatabricksClient:
    """DatabricksClient with the SDK client replaced by a mock."""
    monkeypatch.setenv("DATABRICKS_HOST", "https://test.databricks.com")
    monkeypatch.setenv("DATABRICKS_CLIENT_ID", "client-id")
    monkeypatch.setenv("DATABRICKS_CLIENT_SECRET", "client-secret")
    c = DatabricksClient()
    # Inject mock directly into the cached_property slot, avoiding lambda/patch hacks
    c.__dict__["client"] = mock_workspace
    return c


# -- Tests --------------------------------------------------------------------


class TestDatabricksClientHost:
    def test_host_returns_configured_value(self, client: DatabricksClient) -> None:
        assert client.host == "https://test.databricks.com"

    def test_host_raises_when_not_configured(self) -> None:
        c = DatabricksClient()
        c._settings = Settings.model_construct(DATABRICKS_HOST=None)

        with pytest.raises(ValueError, match="DATABRICKS_HOST not configured"):
            _ = c.host


class TestDatabricksClientFindJob:
    def test_find_job_by_name_found(self, client: DatabricksClient, mock_workspace: MagicMock) -> None:
        mock_workspace.jobs.list.return_value = [
            _make_job(100, "Apply Contract - orders"),
            _make_job(200, "Apply Contract - customers"),
        ]

        assert client.find_job_by_name("orders") == 100

    def test_find_job_by_name_not_found(self, client: DatabricksClient, mock_workspace: MagicMock) -> None:
        mock_workspace.jobs.list.return_value = [_make_job(100, "Other Job")]

        assert client.find_job_by_name("nonexistent") is None

    def test_find_job_skips_job_without_settings(self, client: DatabricksClient, mock_workspace: MagicMock) -> None:
        mock_workspace.jobs.list.return_value = [
            _make_job(100, None),  # no settings
            _make_job(200, "Apply Contract - orders"),
        ]

        assert client.find_job_by_name("orders") == 200


class TestDatabricksClientTriggerJob:
    def test_trigger_job_returns_run_id(self, client: DatabricksClient, mock_workspace: MagicMock) -> None:
        mock_workspace.jobs.run_now.return_value = _make_run(run_id=999)

        assert client.trigger_job(123, "orders_v1") == 999

    def test_trigger_job_raises_on_none_run_id(self, client: DatabricksClient, mock_workspace: MagicMock) -> None:
        mock_workspace.jobs.run_now.return_value = _make_run(run_id=None)

        with pytest.raises(RuntimeError, match="Failed to trigger job"):
            client.trigger_job(123, "orders_v1")


class TestDatabricksClientGetRunUrl:
    def test_get_run_url(self, client: DatabricksClient) -> None:
        url = client.get_run_url(123, 456)
        assert url == "https://test.databricks.com/#job/123/run/456"

    def test_get_run_url_strips_trailing_slash(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATABRICKS_HOST", "https://test.databricks.com/")
        c = DatabricksClient()
        assert c.get_run_url(1, 2) == "https://test.databricks.com/#job/1/run/2"
