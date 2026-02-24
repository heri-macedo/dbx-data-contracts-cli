"""
Contract to Purview mapper service.

Maps Contract models to Purview entity models for Databricks Unity Catalog.

Example:
    >>> from databricks_contracts.services.purview import ContractToPurviewMapper
    >>> mapper = ContractToPurviewMapper()
    >>> purview_entity = mapper.map_contract_to_purview_entity(contract)
"""

from pydantic import ValidationError

from databricks_contracts.config import get_settings
from databricks_contracts.config.logger import get_logger
from databricks_contracts.exceptions import PurviewContractMappingError
from databricks_contracts.models.contracts import Column, Contract
from databricks_contracts.models.purview import (
    PurviewClassification,
    PurviewColumnAttributes,
    PurviewColumnEntity,
    PurviewTableAttributes,
    PurviewTableEntity,
)

logger = get_logger(__name__)


class ContractToPurviewMapper:
    """
    Maps Contract models to Purview entity models.

    This service transforms data contracts into Purview-compatible
    entity models for databricks_table and databricks_table_column types.

    Example:
        >>> mapper = ContractToPurviewMapper()
        >>> purview_entity = mapper.map_contract_to_purview_entity(contract)
        >>> payload = purview_entity.to_json()
    """

    def __init__(self) -> None:
        """
        Initialize the mapper.
        """
        settings = get_settings()
        self._qualified_name_prefix = settings.PURVIEW_QUALIFIED_NAME_PREFIX
        self._table_type_name = settings.PURVIEW_TABLE_TYPE_NAME
        self._column_type_name = settings.PURVIEW_COLUMN_TYPE_NAME

    def map_contract_to_purview_entity(self, contract: Contract) -> PurviewTableEntity:
        """
        Convert a Contract to a PurviewTableEntity.

        This is the main entry point for mapping. It transforms all contract
        data into Purview entity format, including table attributes and columns.

        Args:
            contract: Contract model to convert.

        Returns:
            PurviewTableEntity ready for Purview API.

        Raises:
            PurviewContractMappingError: If mapping fails due to invalid/missing data.

        Example:
            >>> entity = mapper.map_contract_to_purview_entity(contract)
            >>> payload = entity.to_json()
        """
        logger.debug("Mapping contract '%s' to Purview entity", contract.name)

        try:
            column_entities = [
                self._map_column_to_purview_column(column, contract, idx)
                for idx, column in enumerate(contract.table.columns)
            ]

            purview_entity = PurviewTableEntity(
                typeName=self._table_type_name,
                attributes=self._map_contract_to_table_attributes(contract),
                columns=column_entities,
            )

            logger.debug(
                "Successfully mapped contract '%s' to Purview entity with %d columns",
                contract.name,
                len(column_entities),
            )

            return purview_entity

        except ValidationError as e:
            logger.error("Pydantic validation failed while mapping contract '%s': %s", contract.name, e)
            raise PurviewContractMappingError(f"Failed to map contract '{contract.name}' to Purview entity: {e}") from e

        except AttributeError as e:
            logger.error("Missing attribute while mapping contract '%s': %s", contract.name, e)
            raise PurviewContractMappingError(f"Contract '{contract.name}' is missing a required attribute: {e}") from e

        except Exception as e:
            logger.error("Unexpected error while mapping contract '%s': %s", contract.name, e)
            raise PurviewContractMappingError(f"Unexpected error mapping contract '{contract.name}': {e}") from e

    def _build_table_qualified_name(self, contract: Contract) -> str:
        """
        Build the Purview qualified name for a table.

        Format: prefix + catalog/schema/table (matching Databricks UC scan format)

        Args:
            contract: Contract containing table information.

        Returns:
            Qualified name in format: databricks://metastore/catalog/schema/table

        Example:
            >>> mapper._build_table_qualified_name(contract)
            "databricks://metastore/my_catalog/my_schema/my_table"
        """
        return f"{self._qualified_name_prefix}{contract.catalog}/{contract.schema_name}/{contract.table.name}"

    def _build_column_qualified_name(self, column: Column, contract: Contract) -> str:
        """
        Build the Purview qualified name for a column.

        Args:
            column: Column to build qualified name for.
            contract: Parent contract containing table information.

        Returns:
            Qualified name in format: table_qualified_name#column_name

        Example:
            >>> mapper._build_column_qualified_name(column, contract)
            "databricks://metastore/my_catalog/my_schema/my_table#customer_id"
        """
        table_qualified_name = self._build_table_qualified_name(contract)
        return f"{table_qualified_name}#{column.name}"

    def _build_table_tags(self, contract: Contract) -> dict[str, str]:
        """
        Build the tags map for a table entity.

        Includes ownership, governance, and table metadata.

        Args:
            contract: Contract to extract tags from.

        Returns:
            Dict with tag key-value pairs.
        """
        tags: dict[str, str] = {
            "portfolio": contract.ownership.portfolio.value,
            "sub_domain": contract.ownership.sub_domain.value,
            "layer": contract.table.tags.layer.value,
            "data_owner": contract.ownership.data_owner,
            "bds": contract.ownership.bds,
            "tds": contract.ownership.tds,
            "contract_version": contract.version,
            "refresh_frequency": contract.table.refresh_frequency.value,
            "retention_days": str(contract.table.retention_days),
        }

        # Add classification if present
        if contract.table.tags.classification:
            tags["classification"] = contract.table.tags.classification.value

        # Add data_exchange if present
        if contract.table.tags.data_exchange:
            tags["data_exchange"] = contract.table.tags.data_exchange

        return tags

    def _map_contract_to_table_attributes(self, contract: Contract) -> PurviewTableAttributes:
        """
        Map contract data to Purview table attributes.

        Args:
            contract: Contract to extract attributes from.

        Returns:
            PurviewTableAttributes with all mapped fields.
        """
        return PurviewTableAttributes(
            qualifiedName=self._build_table_qualified_name(contract),
            name=contract.table.name,
            catalogName=contract.catalog,
            schemaName=contract.schema_name,
            comment=contract.table.description,
            tableType="MANAGED",
            tags=self._build_table_tags(contract),
        )

    def _build_column_classifications(self, column: Column) -> list[PurviewClassification]:
        """
        Build the classifications list for a column entity.

        Maps privacy tags (PII_ENCRYPTED, PII_HIDDEN) to Purview classifications.

        Args:
            column: Column to extract classifications from.

        Returns:
            List of PurviewClassification objects.
        """
        classifications: list[PurviewClassification] = []

        if column.tags and column.tags.privacy:
            # Map privacy tag to Purview classification
            # Values: PII_ENCRYPTED or PII_HIDDEN
            classifications.append(PurviewClassification(typeName=column.tags.privacy.value))

        return classifications

    def _map_column_to_purview_column(
        self,
        column: Column,
        contract: Contract,
        position: int,
    ) -> PurviewColumnEntity:
        """
        Map a single column to a Purview column entity.

        Args:
            column: Column to map.
            contract: Parent contract for context (qualified name generation).
            position: Column ordinal position (0-based).

        Returns:
            PurviewColumnEntity with attributes and classifications.
        """
        column_attributes = PurviewColumnAttributes(
            qualifiedName=self._build_column_qualified_name(column, contract),
            name=column.name,
            dataType=column.type.upper(),
            isNullable=column.nullable,
            ordinalPosition=position,
            comment=column.description,
        )

        return PurviewColumnEntity(
            typeName=self._column_type_name,
            attributes=column_attributes,
            classifications=self._build_column_classifications(column),
        )
