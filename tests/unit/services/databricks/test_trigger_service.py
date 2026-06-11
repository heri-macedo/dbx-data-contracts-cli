"""Unit tests for TriggerService with mocked DatabricksClient."""

from unittest.mock import MagicMock

from databricks_contracts.services.databricks.trigger import TriggerService


class TestTriggerServiceTrigger:
    def test_trigger_dry_run(self) -> None:
        client = MagicMock()
        service = TriggerService(client=client, dry_run=True)
        result = service.trigger("orders_v1")
        assert result.success is True
        assert "DRY RUN" in result.error
        client.find_job_by_name.assert_not_called()

    def test_trigger_job_found_and_triggered(self) -> None:
        client = MagicMock()
        client.find_job_by_name.return_value = 42
        client.trigger_job.return_value = 999
        client.get_run_url.return_value = "https://db.com/#job/42/run/999"
        service = TriggerService(client=client, dry_run=False)

        result = service.trigger("orders_v1")
        assert result.success is True
        assert result.run_id == 999
        assert result.run_url == "https://db.com/#job/42/run/999"

    def test_trigger_job_not_found(self) -> None:
        client = MagicMock()
        client.find_job_by_name.return_value = None
        service = TriggerService(client=client, dry_run=False)

        result = service.trigger("nonexistent")
        assert result.success is False
        assert "Job not found" in result.error

    def test_trigger_exception(self) -> None:
        client = MagicMock()
        client.find_job_by_name.side_effect = Exception("Connection error")
        service = TriggerService(client=client, dry_run=False)

        result = service.trigger("orders_v1")
        assert result.success is False
        assert "Connection error" in result.error


class TestTriggerServiceBatch:
    def test_trigger_batch(self) -> None:
        client = MagicMock()
        client.find_job_by_name.return_value = 42
        client.trigger_job.return_value = 100
        client.get_run_url.return_value = "https://url"
        service = TriggerService(client=client, dry_run=False)

        results = service.trigger_batch(["a", "b"])
        assert len(results) == 2
        assert all(r.success for r in results)
