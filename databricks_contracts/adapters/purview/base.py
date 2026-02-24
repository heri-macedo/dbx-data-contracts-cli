"""
Base Purview client interface.

Abstract base class defining the contract for Purview API clients.

Example:
    >>> from databricks_contracts.adapters.purview import BasePurviewClient
    >>> class MyClient(BasePurviewClient):
    ...     def create_or_update_entity(self, payload, collection): ...
"""

from abc import ABC, abstractmethod


class BasePurviewClient(ABC):
    """
    Abstract base class for Purview catalog clients.

    All Purview client implementations must inherit from this class
    and implement its abstract methods.

    This allows for:
    - Easy swapping between real and dry-run implementations
    - Dependency injection in handlers and services
    - Consistent interface across all client types

    Example:
        >>> class CustomClient(BasePurviewClient):
        ...     def create_or_update_entity(self, payload, collection):
        ...         return {"guid": "custom-guid"}
    """

    @abstractmethod
    def create_or_update_entity(
        self,
        entity_payload: dict,
        collection_name: str,
        collection_id: str,
    ) -> dict:
        """
        Create or update an entity in Purview catalog.

        If an entity with the same qualifiedName exists, it will be updated.
        Otherwise, a new entity will be created.

        Args:
            entity_payload: Entity payload from PurviewTableEntity.to_json().
            collection_name: Purview collection friendly name (for logging).
            collection_id: Purview collection ID (passed as query parameter to API).

        Returns:
            Response dict from Purview API containing:
            - guidAssignments: Map of qualifiedName to GUID for new entities
            - mutatedEntities: Details of created/updated entities

        Raises:
            PurviewAuthenticationError: If authentication fails (401/403).
            PurviewConnectionError: If connection to Purview fails.
            PurviewCollectionNotFoundError: If collection doesn't exist (404).
            PurviewEntityOperationError: If entity operation fails (400/500).

        Example:
            >>> payload = entity.to_json()
            >>> response = client.create_or_update_entity(payload, "MyCollection", "abc123")
            >>> guid = response["guidAssignments"]["databricks://..."]
        """
        ...

    @abstractmethod
    def get_collection_id_by_friendly_name(self, friendly_name: str) -> tuple[str, str]:
        """
        Get the collection ID by its friendly name.

        The collection ID (name field) is required for assigning entities to collections.
        This method searches all collections and matches by friendly name.

        If not found, falls back to root collection.

        Args:
            friendly_name: The friendly name of the collection (from contract YAML).

        Returns:
            Tuple of (collection_id, display_name):
                - collection_id: The collection ID to use in entity payloads
                - display_name: Name to display in output (includes "(root)" if fallback)

        Example:
            >>> collection_id, display_name = client.get_collection_id_by_friendly_name("TestCollection")
        """
        ...
