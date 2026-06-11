"""Unit tests for ContractToPurviewMapper."""

import pytest

from databricks_contracts.exceptions import PurviewContractMappingError
from databricks_contracts.models.contracts.contract import Contract
from databricks_contracts.services.purview.contract_to_purview_mapper import ContractToPurviewMapper

# -- Helpers ------------------------------------------------------------------


class ContractWithBrokenTable:
    """Simulates a contract whose .table property raises AttributeError."""

    name = "broken_contract"

    @property
    def table(self):
        raise AttributeError("table attribute is missing")


class ContractWithUnexpectedError:
    """Simulates a contract whose .table property raises an unexpected error."""

    name = "broken_contract"

    @property
    def table(self):
        raise RuntimeError("something went very wrong")


# -- Tests --------------------------------------------------------------------


class TestContractToPurviewMapper:
    def test_map_contract_to_purview_entity(self, sample_contract_data: dict) -> None:
        contract = Contract.model_validate(sample_contract_data)
        mapper = ContractToPurviewMapper()
        entity = mapper.map_contract_to_purview_entity(contract)

        assert entity.typeName == "databricks_table"
        assert entity.attributes.name == "test_table"
        assert entity.attributes.catalogName == "test_catalog"
        assert entity.attributes.schemaName == "test_schema"
        assert len(entity.columns) == 2
        assert entity.columns[0].attributes.name == "id"

    def test_builds_correct_qualified_name(self, sample_contract_data: dict) -> None:
        contract = Contract.model_validate(sample_contract_data)
        mapper = ContractToPurviewMapper()
        entity = mapper.map_contract_to_purview_entity(contract)

        assert "test_catalog/test_schema/test_table" in entity.attributes.qualifiedName

    def test_column_qualified_name_format(self, sample_contract_data: dict) -> None:
        contract = Contract.model_validate(sample_contract_data)
        mapper = ContractToPurviewMapper()
        entity = mapper.map_contract_to_purview_entity(contract)

        col_qn = entity.columns[0].attributes.qualifiedName
        assert "#id" in col_qn

    def test_table_tags_include_metadata(self, sample_contract_data: dict) -> None:
        contract = Contract.model_validate(sample_contract_data)
        mapper = ContractToPurviewMapper()
        entity = mapper.map_contract_to_purview_entity(contract)

        tags = entity.attributes.tags
        assert tags["portfolio"] == "Portfolio_1"
        assert tags["layer"] == "Gold"
        assert tags["retention_days"] == "90"
        assert tags["data_owner"] == "test@example.com"

    def test_table_tags_with_classification(self, sample_contract_data: dict) -> None:
        sample_contract_data["table"]["tags"]["classification"] = "Classification_1"
        contract = Contract.model_validate(sample_contract_data)
        mapper = ContractToPurviewMapper()
        entity = mapper.map_contract_to_purview_entity(contract)

        assert entity.attributes.tags["classification"] == "Classification_1"

    def test_table_tags_with_data_exchange(self, sample_contract_data: dict) -> None:
        sample_contract_data["table"]["tags"]["data_exchange"] = "my_exchange"
        contract = Contract.model_validate(sample_contract_data)
        mapper = ContractToPurviewMapper()
        entity = mapper.map_contract_to_purview_entity(contract)

        assert entity.attributes.tags["data_exchange"] == "my_exchange"

    def test_column_with_privacy_classification(self, sample_contract_data: dict) -> None:
        sample_contract_data["table"]["columns"][0]["tags"] = {"privacy": "PII_ENCRYPTED"}
        contract = Contract.model_validate(sample_contract_data)
        mapper = ContractToPurviewMapper()
        entity = mapper.map_contract_to_purview_entity(contract)

        assert len(entity.columns[0].classifications) == 1
        assert entity.columns[0].classifications[0].typeName == "PII_ENCRYPTED"

    def test_mapping_attribute_error_raises(self) -> None:
        mapper = ContractToPurviewMapper()

        with pytest.raises(PurviewContractMappingError, match="missing a required attribute"):
            mapper.map_contract_to_purview_entity(ContractWithBrokenTable())  # type: ignore

    def test_mapping_unexpected_error_raises(self) -> None:
        mapper = ContractToPurviewMapper()

        with pytest.raises(PurviewContractMappingError, match="Unexpected error"):
            mapper.map_contract_to_purview_entity(ContractWithUnexpectedError())  # type: ignore
