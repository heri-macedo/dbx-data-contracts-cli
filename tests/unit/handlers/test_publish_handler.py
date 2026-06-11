"""Unit tests for PublishHandler with mocked services."""

from unittest.mock import MagicMock

from databricks_contracts.exceptions import (
    ContractNotFoundError,
    ContractParseError,
    ContractValidationError,
    PurviewAuthenticationError,
    PurviewCollectionNotFoundError,
    PurviewConnectionError,
    PurviewContractMappingError,
    PurviewEntityOperationError,
    PurviewError,
)
from databricks_contracts.handlers.publish_handler import PublishHandler
from databricks_contracts.models.inputs.publish_input import PublishInput
from databricks_contracts.models.results.publish_result import PublishResult


def _make_handler(
    load_side_effect=None,
    publish_result=None,
    modified_contracts=None,
    all_contracts=None,
) -> PublishHandler:
    loader = MagicMock()
    if load_side_effect:
        loader.load.side_effect = load_side_effect
    else:
        loader.load.return_value = MagicMock(name="test_contract", version="1.0")
    loader.list_contracts.return_value = all_contracts or []

    publisher = MagicMock()
    if publish_result:
        publisher.publish_contract_to_purview.return_value = publish_result
    else:
        publisher.publish_contract_to_purview.return_value = PublishResult(
            contract_name="test_contract",
            success=True,
            purview_qualified_name="databricks://m/c/s/t",
        )

    change_detector = MagicMock()
    change_detector.get_modified_contracts.return_value = modified_contracts or []

    return PublishHandler(loader, publisher, change_detector)


class TestPublishHandlerHandle:
    def test_success(self) -> None:
        handler = _make_handler()
        result = handler.handle(PublishInput(contract_name="test_contract"))
        assert result.success is True

    def test_contract_not_found(self) -> None:
        handler = _make_handler(load_side_effect=ContractNotFoundError("test_contract"))
        result = handler.handle(PublishInput(contract_name="test_contract"))
        assert result.success is False
        assert "not found" in result.error

    def test_contract_parse_error(self) -> None:
        handler = _make_handler(load_side_effect=ContractParseError("bad yaml"))
        result = handler.handle(PublishInput(contract_name="test_contract"))
        assert result.success is False
        assert "parse" in result.error.lower()

    def test_contract_validation_error(self) -> None:
        handler = _make_handler(load_side_effect=ContractValidationError("invalid"))
        result = handler.handle(PublishInput(contract_name="test_contract"))
        assert result.success is False
        assert "validation" in result.error.lower()

    def test_purview_mapping_error(self) -> None:
        loader = MagicMock()
        loader.load.return_value = MagicMock()
        publisher = MagicMock()
        publisher.publish_contract_to_purview.side_effect = PurviewContractMappingError("mapping fail")
        handler = PublishHandler(loader, publisher, MagicMock())
        result = handler.handle(PublishInput(contract_name="test_contract"))
        assert result.success is False
        assert "Mapping" in result.error

    def test_purview_auth_error(self) -> None:
        loader = MagicMock()
        loader.load.return_value = MagicMock()
        publisher = MagicMock()
        publisher.publish_contract_to_purview.side_effect = PurviewAuthenticationError("auth fail")
        handler = PublishHandler(loader, publisher, MagicMock())
        result = handler.handle(PublishInput(contract_name="test_contract"))
        assert result.success is False
        assert "authentication" in result.error.lower()

    def test_purview_connection_error(self) -> None:
        loader = MagicMock()
        loader.load.return_value = MagicMock()
        publisher = MagicMock()
        publisher.publish_contract_to_purview.side_effect = PurviewConnectionError("conn fail")
        handler = PublishHandler(loader, publisher, MagicMock())
        result = handler.handle(PublishInput(contract_name="test_contract"))
        assert result.success is False
        assert "Connection" in result.error

    def test_purview_collection_not_found(self) -> None:
        loader = MagicMock()
        loader.load.return_value = MagicMock()
        publisher = MagicMock()
        publisher.publish_contract_to_purview.side_effect = PurviewCollectionNotFoundError("coll missing")
        handler = PublishHandler(loader, publisher, MagicMock())
        result = handler.handle(PublishInput(contract_name="test_contract"))
        assert result.success is False
        assert "coll missing" in result.error

    def test_purview_entity_operation_error(self) -> None:
        loader = MagicMock()
        loader.load.return_value = MagicMock()
        publisher = MagicMock()
        publisher.publish_contract_to_purview.side_effect = PurviewEntityOperationError("op fail")
        handler = PublishHandler(loader, publisher, MagicMock())
        result = handler.handle(PublishInput(contract_name="test_contract"))
        assert result.success is False
        assert "operation" in result.error.lower()

    def test_generic_purview_error(self) -> None:
        loader = MagicMock()
        loader.load.return_value = MagicMock()
        publisher = MagicMock()
        publisher.publish_contract_to_purview.side_effect = PurviewError("generic purview")
        handler = PublishHandler(loader, publisher, MagicMock())
        result = handler.handle(PublishInput(contract_name="test_contract"))
        assert result.success is False
        assert "generic purview" in result.error

    def test_unexpected_error(self) -> None:
        loader = MagicMock()
        loader.load.return_value = MagicMock()
        publisher = MagicMock()
        publisher.publish_contract_to_purview.side_effect = RuntimeError("boom")
        handler = PublishHandler(loader, publisher, MagicMock())
        result = handler.handle(PublishInput(contract_name="test_contract"))
        assert result.success is False
        assert "Unexpected" in result.error


class TestPublishHandlerHandleModified:
    def test_no_modified_contracts(self) -> None:
        handler = _make_handler(modified_contracts=[])
        results = handler.handle_modified()
        assert results == []

    def test_modified_contracts_published(self) -> None:
        handler = _make_handler(modified_contracts=["a", "b"])
        results = handler.handle_modified()
        assert len(results) == 2
        assert all(r.success for r in results)


class TestPublishHandlerHandleAll:
    def test_no_contracts(self) -> None:
        handler = _make_handler(all_contracts=[])
        results = handler.handle_all()
        assert results == []

    def test_all_contracts_published(self) -> None:
        handler = _make_handler(all_contracts=["x", "y"])
        results = handler.handle_all()
        assert len(results) == 2
