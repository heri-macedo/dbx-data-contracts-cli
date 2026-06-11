"""Unit tests for TriggerHandler with mocked services."""

from unittest.mock import MagicMock

from databricks_contracts.handlers.trigger_handler import TriggerHandler
from databricks_contracts.models.inputs.trigger_input import TriggerInput
from databricks_contracts.models.results.trigger_result import TriggerResult


def _make_handler(
    trigger_results: list[TriggerResult] | None = None,
    modified_contracts: list[str] | None = None,
    all_contracts: list[str] | None = None,
) -> TriggerHandler:
    trigger_service = MagicMock()
    trigger_service.trigger_batch.return_value = trigger_results or []
    change_detector = MagicMock()
    change_detector.get_modified_contracts.return_value = modified_contracts or []
    loader = MagicMock()
    loader.list_contracts.return_value = all_contracts or []
    return TriggerHandler(trigger_service, change_detector, loader)


class TestTriggerHandlerHandle:
    def test_handle_triggers_contracts(self) -> None:
        expected = [
            TriggerResult(contract_name="orders", success=True, run_id=1, run_url="url1"),
            TriggerResult(contract_name="customers", success=True, run_id=2, run_url="url2"),
        ]
        handler = _make_handler(trigger_results=expected)
        results = handler.handle(TriggerInput(contracts=["orders", "customers"]))
        assert len(results) == 2
        assert results[0].success is True


class TestTriggerHandlerHandleModified:
    def test_handle_modified_no_changes(self) -> None:
        handler = _make_handler(modified_contracts=[])
        results = handler.handle_modified(base_ref="HEAD~1")
        assert results == []

    def test_handle_modified_with_changes(self) -> None:
        expected = [TriggerResult(contract_name="orders", success=True, run_id=1, run_url="url")]
        handler = _make_handler(trigger_results=expected, modified_contracts=["orders"])
        results = handler.handle_modified()
        assert len(results) == 1


class TestTriggerHandlerHandleAll:
    def test_handle_all_empty(self) -> None:
        handler = _make_handler(all_contracts=[])
        results = handler.handle_all()
        assert results == []

    def test_handle_all_triggers_all(self) -> None:
        expected = [
            TriggerResult(contract_name="a", success=True),
            TriggerResult(contract_name="b", success=False, error="fail"),
        ]
        handler = _make_handler(trigger_results=expected, all_contracts=["a", "b"])
        results = handler.handle_all()
        assert len(results) == 2
