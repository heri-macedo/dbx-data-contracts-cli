"""Unit tests for TableTags.to_dict — data_exchange coverage."""

from databricks_contracts.models.contracts.enums import Classification, Layer
from databricks_contracts.models.contracts.table import TableTags


class TestTableTagsToDict:
    """Tests for TableTags.to_dict() method."""

    def test_layer_only(self) -> None:
        tags = TableTags(layer=Layer.GOLD)
        assert tags.to_dict() == {"layer": "Gold"}

    def test_with_classification(self) -> None:
        tags = TableTags(layer=Layer.SILVER, classification=Classification.CLASSIFICATION_1)
        result = tags.to_dict()
        assert result == {"layer": "Silver", "classification": "Classification_1"}

    def test_with_data_exchange(self) -> None:
        tags = TableTags(layer=Layer.BRONZE, data_exchange="exchange_flag")
        result = tags.to_dict()
        assert result == {"layer": "Bronze", "data_exchange": "exchange_flag"}

    def test_with_all_fields(self) -> None:
        tags = TableTags(
            layer=Layer.GOLD,
            classification=Classification.CLASSIFICATION_2,
            data_exchange="my_exchange",
        )
        result = tags.to_dict()
        assert result == {
            "layer": "Gold",
            "classification": "Classification_2",
            "data_exchange": "my_exchange",
        }
