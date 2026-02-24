"""
Purview publisher service.

Orchestrates publishing contracts to Microsoft Purview catalog.

Example:
    >>> from databricks_contracts.services.purview import PurviewPublisherService
    >>> publisher = PurviewPublisherService(mapper, client)
    >>> result = publisher.publish_contract_to_purview(contract)
"""

from databricks_contracts.adapters.purview.base import BasePurviewClient
from databricks_contracts.config import get_settings
from databricks_contracts.config.logger import get_logger
from databricks_contracts.models.contracts import Contract
from databricks_contracts.models.results import PublishResult
from databricks_contracts.services.purview.contract_to_purview_mapper import ContractToPurviewMapper

logger = get_logger(__name__)


class PurviewPublisherService:
    """
    Service for publishing contracts to Microsoft Purview.

    Orchestrates the mapping of contracts to Purview entities and
    their publication to the Purview catalog API.

    Attributes:
        mapper: Service for mapping contracts to Purview entities.
        client: Purview API client for catalog operations.

    Example:
        >>> mapper = ContractToPurviewMapper()
        >>> client = PurviewApiClient.from_environment_variables()
        >>> publisher = PurviewPublisherService(mapper, client)
        >>> result = publisher.publish_contract_to_purview(contract)
    """

    def __init__(
        self,
        contract_to_purview_mapper: ContractToPurviewMapper,
        purview_client: BasePurviewClient,
    ) -> None:
        """
        Initialize the publisher service.

        Args:
            contract_to_purview_mapper: Mapper for converting contracts to Purview entities.
            purview_client: Client for Purview API operations.

        Example:
            >>> publisher = PurviewPublisherService(mapper, client)
        """
        self._mapper = contract_to_purview_mapper
        self._client = purview_client
        self._qualified_name_prefix = get_settings().PURVIEW_QUALIFIED_NAME_PREFIX

    def publish_contract_to_purview(self, contract: Contract) -> PublishResult:
        """
        Publish a contract to Microsoft Purview.

        This method:
        1. Maps the contract to a Purview entity
        2. Sends the entity to Purview API
        3. Returns the result

        Args:
            contract: Contract to publish.

        Returns:
            PublishResult with success status and Purview entity details.

        Raises:
            PurviewContractMappingError: If mapping fails (from mapper).
            PurviewAuthenticationError: If authentication fails (from client).
            PurviewConnectionError: If connection fails (from client).
            PurviewCollectionNotFoundError: If collection doesn't exist (from client).
            PurviewEntityOperationError: If entity operation fails (from client).

        Example:
            >>> result = publisher.publish_contract_to_purview(contract)
            >>> if result.success:
            ...     print(f"Published to: {result.purview_qualified_name}")
        """
        collection_friendly_name = contract.ownership.purview_collection
        qualified_name = f"{self._qualified_name_prefix}{contract.full_table_name}"

        logger.info(
            "Publishing contract '%s' to Purview collection '%s'",
            contract.name,
            collection_friendly_name,
        )

        # 1. Look up collection ID by friendly name (falls back to root if not found)
        logger.debug("Looking up collection ID for '%s'...", collection_friendly_name)
        collection_id, collection_display_name = self._client.get_collection_id_by_friendly_name(
            collection_friendly_name
        )
        logger.debug("Using collection: '%s' (ID: '%s')", collection_display_name, collection_id)

        # 2. Map contract to Purview entity (may raise PurviewContractMappingError)
        logger.debug("Mapping contract to Purview entity...")
        purview_entity = self._mapper.map_contract_to_purview_entity(contract)

        # 3. Generate API payload (table + columns) with collection ID
        api_payload = purview_entity.to_json()

        # 4. Send to Purview (may raise Purview*Error)
        logger.debug("Sending entity to Purview API...")
        self._client.create_or_update_entity(
            entity_payload=api_payload,
            collection_name=collection_friendly_name,
            collection_id=collection_id,
        )

        logger.info(
            "Successfully published contract '%s' to Purview (qualified_name: %s)",
            contract.name,
            qualified_name,
        )

        return PublishResult(
            contract_name=contract.name,
            success=True,
            purview_collection_name=collection_display_name,
            purview_qualified_name=qualified_name,
        )
