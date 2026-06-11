"""Unit tests for PurviewPublisherService with mocked dependencies."""

from unittest.mock import MagicMock

from databricks_contracts.models.contracts.contract import Contract
from databricks_contracts.services.purview.purview_publisher import PurviewPublisherService


class TestPurviewPublisherService:
    def test_publish_contract_success(self, sample_contract_data: dict) -> None:
        contract = Contract.model_validate(sample_contract_data)

        mapper = MagicMock()
        mock_entity = MagicMock()
        mock_entity.to_json.return_value = {"entities": [{"attributes": {"qualifiedName": "qn"}}]}
        mapper.map_contract_to_purview_entity.return_value = mock_entity

        client = MagicMock()
        client.get_collection_id_by_friendly_name.return_value = ("coll-id", "TestCollection")
        client.create_or_update_entity.return_value = {"guidAssignments": {}}

        publisher = PurviewPublisherService(
            contract_to_purview_mapper=mapper,
            purview_client=client,
        )
        result = publisher.publish_contract_to_purview(contract)

        assert result.success is True
        assert result.contract_name == "test_contract"
        assert result.purview_collection_name == "TestCollection"
        mapper.map_contract_to_purview_entity.assert_called_once_with(contract)
        client.create_or_update_entity.assert_called_once()
