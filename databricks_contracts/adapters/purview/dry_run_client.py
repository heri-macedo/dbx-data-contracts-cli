"""
Dry-run Purview client for preview mode.

Simulates Purview API operations without making real API calls.
Used when --dry-run flag is passed to CLI commands.

Example:
    >>> from databricks_contracts.adapters.purview import DryRunPurviewClient
    >>> client = DryRunPurviewClient()
    >>> response = client.create_or_update_entity(payload, "MyCollection")
"""

import uuid

from databricks_contracts.adapters.purview.base import BasePurviewClient
from databricks_contracts.config.logger import get_logger

logger = get_logger(__name__)


class DryRunPurviewClient(BasePurviewClient):
    """
    Dry-run client for Purview API operations.

    Used when --dry-run flag is passed. Logs what would happen
    without actually contacting Purview API.

    Example:
        >>> client = DryRunPurviewClient()
        >>> response = client.create_or_update_entity(payload, "MyCollection")
        >>> # Logs what would be published, returns simulated response
    """

    def __init__(self) -> None:
        """
        Initialize the dry-run client.

        Example:
            >>> client = DryRunPurviewClient()
        """
        pass

    def create_or_update_entity(
        self,
        entity_payload: dict,
        collection_name: str,
        collection_id: str,
    ) -> dict:
        """
        Simulate creating/updating an entity in Purview.

        Logs what would be published and returns a simulated response.

        Args:
            entity_payload: Entity payload that would be sent to Purview.
            collection_name: Collection friendly name (for logging).
            collection_id: Collection ID that would be used as query parameter.

        Returns:
            Simulated response dict matching Purview API structure.

        Example:
            >>> response = client.create_or_update_entity(payload, "MyCollection", "abc123")
        """
        entities = entity_payload["entities"]

        logger.info("🔶 [DRY-RUN] Would publish %d entities to Purview:", len(entities))
        logger.info("🔶 [DRY-RUN]   Collection: %s (ID: %s)", collection_name, collection_id)

        guid_assignments = {}
        created_entities = []

        for entity_data in entities:
            attributes = entity_data["attributes"]
            qualified_name = attributes["qualifiedName"]
            type_name = entity_data.get("typeName", "unknown")

            logger.info("🔶 [DRY-RUN]   - %s: %s", type_name, qualified_name)

            simulated_guid = f"dry-run-guid-{uuid.uuid4().hex[:12]}"
            guid_assignments[qualified_name] = simulated_guid
            created_entities.append(
                {
                    "guid": simulated_guid,
                    "typeName": type_name,
                    "attributes": {"qualifiedName": qualified_name},
                }
            )

        return {
            "guidAssignments": guid_assignments,
            "mutatedEntities": {"CREATE": created_entities},
        }

    def get_collection_id_by_friendly_name(self, friendly_name: str) -> tuple[str, str]:
        """
        Simulate getting collection ID by friendly name.

        In dry-run mode, returns the friendly name as the collection ID
        since we don't actually query Purview.

        Args:
            friendly_name: The friendly name of the collection.

        Returns:
            Tuple of (collection_id, display_name) - both simulated.
        """
        logger.info(
            "🔶 [DRY-RUN] Would look up collection ID for friendly name: '%s'",
            friendly_name,
        )
        # In dry-run mode, just return the friendly name as the ID
        return f"dry-run-collection-{friendly_name}", friendly_name
