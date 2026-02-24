"""
Purview Catalog API client using official Azure SDK.

Uses azure-purview-catalog and azure-identity packages for
authentication and API operations. Configuration is loaded
from environment variables via Settings.

API Documentation:
    - Entity Create/Update: https://learn.microsoft.com/en-us/rest/api/purview/datamapdataplane/entity/create-or-update
    - List Collections: https://learn.microsoft.com/en-us/rest/api/purview/accountdataplane/collections/list-collections

Example:
    >>> from databricks_contracts.adapters.purview import PurviewCatalogApiClient
    >>> client = PurviewCatalogApiClient()
    >>> response = client.create_or_update_entity(payload, "MyCollection", "abc123")
"""

from functools import cached_property

from azure.core.credentials import TokenCredential
from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ServiceRequestError,
)
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.purview.administration.account import PurviewAccountClient
from azure.purview.catalog import PurviewCatalogClient

from databricks_contracts.adapters.purview.base import BasePurviewClient
from databricks_contracts.config import get_settings
from databricks_contracts.config.logger import get_logger
from databricks_contracts.exceptions import (
    PurviewAuthenticationError,
    PurviewCollectionNotFoundError,
    PurviewConnectionError,
    PurviewEntityOperationError,
)

logger = get_logger(__name__)


class PurviewCatalogApiClient(BasePurviewClient):
    """
    Client for Azure Purview Catalog API using official SDK.

    Uses azure-purview-catalog and azure-identity packages for
    authentication and API operations. Configuration is loaded
    from environment variables via Settings.

    Example:
        >>> client = PurviewCatalogApiClient()
        >>> response = client.create_or_update_entity(payload, "DataContracts")
        >>> print(response["guidAssignments"])
    """

    def __init__(self) -> None:
        """
        Initialize the Purview client.

        Loads configuration from environment variables via Settings.

        Raises:
            PurviewAuthenticationError: If required environment variables are not set.

        Example:
            >>> client = PurviewCatalogApiClient()
        """
        self._settings = get_settings()

    @property
    def _endpoint(self) -> str:
        """Get Purview API endpoint URL."""
        if not self._settings.PURVIEW_ACCOUNT_NAME:
            raise PurviewAuthenticationError("PURVIEW_ACCOUNT_NAME not configured")
        return f"https://{self._settings.PURVIEW_ACCOUNT_NAME}.purview.azure.com"

    def __validate_if_environment_variables_exists(self) -> bool:
        """
        Validate if the required environment variables for Purview are configured.

        Only PURVIEW_ACCOUNT_NAME is required. Service Principal credentials
        (CLIENT_ID, CLIENT_SECRET, TENANT_ID) are optional - if not provided,
        authentication will fall back to DefaultAzureCredential (az login, etc.).

        Returns:
            True if required environment variables are configured.

        Raises:
            PurviewAuthenticationError: If PURVIEW_ACCOUNT_NAME is missing.
        """
        if not self._settings.PURVIEW_ACCOUNT_NAME:
            raise PurviewAuthenticationError("Missing required environment variable: PURVIEW_ACCOUNT_NAME")
        return True

    def __has_service_principal_credentials(self) -> bool:
        """
        Check if Service Principal credentials are configured.

        Returns:
            True if all Service Principal credentials are available.
        """
        return bool(
            self._settings.PURVIEW_CLIENT_ID
            and self._settings.PURVIEW_CLIENT_SECRET
            and self._settings.PURVIEW_TENANT_ID
        )

    def __get_credential(self) -> TokenCredential:
        """
        Get the credential for the Purview client.

        If Service Principal credentials (CLIENT_ID, CLIENT_SECRET, TENANT_ID) are
        configured, uses ClientSecretCredential.

        Otherwise, falls back to DefaultAzureCredential which tries multiple
        authentication methods in order:
        - Environment variables
        - Managed Identity
        - Azure CLI (az login)
        - Azure PowerShell
        - Interactive browser

        Returns:
            TokenCredential instance for authentication.
        """
        if self.__has_service_principal_credentials():
            logger.debug("Using Service Principal credentials for Purview authentication")
            return ClientSecretCredential(
                tenant_id=self._settings.PURVIEW_TENANT_ID,
                client_id=self._settings.PURVIEW_CLIENT_ID,
                client_secret=self._settings.PURVIEW_CLIENT_SECRET.get_secret_value(),
            )

        logger.debug(
            "Service Principal credentials not configured, using DefaultAzureCredential "
            "(az login, managed identity, etc.)"
        )
        return DefaultAzureCredential()

    @cached_property
    def _client(self) -> PurviewCatalogClient:
        """
        Get the Purview Catalog SDK client (cached on first access).

        Returns:
            Configured PurviewCatalogClient instance.

        Raises:
            PurviewAuthenticationError: If required settings are missing.
        """
        self.__validate_if_environment_variables_exists()
        credential = self.__get_credential()

        logger.debug("Initializing Purview Catalog client for '%s'", self._settings.PURVIEW_ACCOUNT_NAME)
        return PurviewCatalogClient(
            endpoint=self._endpoint,
            credential=credential,
        )

    @cached_property
    def _account_client(self) -> PurviewAccountClient:
        """
        Get the Purview Account SDK client for collection operations (cached on first access).

        Returns:
            Configured PurviewAccountClient instance.

        Raises:
            PurviewAuthenticationError: If required settings are missing.
        """
        self.__validate_if_environment_variables_exists()
        credential = self.__get_credential()

        logger.debug("Initializing Purview Account client for '%s'", self._settings.PURVIEW_ACCOUNT_NAME)
        return PurviewAccountClient(
            endpoint=self._endpoint,
            credential=credential,
        )

    def get_collection_id_by_friendly_name(self, friendly_name: str) -> tuple[str, str]:
        """
        Get the collection ID by its friendly name.

        The collection ID (name field) is required for assigning entities to collections.
        This method searches all collections and matches by friendly name (exact match).

        If the collection is not found, falls back to the root collection (account name)
        with a warning. This ensures entities are always published somewhere.

        API Endpoint:
            GET {endpoint}/account/collections
            https://learn.microsoft.com/en-us/rest/api/purview/accountdataplane/collections/list-collections

        Args:
            friendly_name: The friendly name of the collection (from contract YAML).

        Returns:
            Tuple of (collection_id, display_name):
                - collection_id: The collection ID to use as query parameter
                - display_name: Name to display in output (includes "(root)" if fallback)

        Raises:
            PurviewConnectionError: If connection to Purview fails.
            PurviewAuthenticationError: If authentication fails.

        Example:
            >>> collection_id, display_name = client.get_collection_id_by_friendly_name("TestCollection")
            >>> # Returns ("abcd1234", "TestCollection") if found
            >>> # Or ("account_name", "account_name (root)") if fallback
        """
        logger.debug("Searching for collection with friendly name: '%s'", friendly_name)

        try:
            collections = self._account_client.collections.list_collections()

            for collection in collections:
                if collection.get("friendlyName", "") == friendly_name:
                    collection_id = collection.get("name")
                    logger.debug(
                        "Found collection '%s' with ID '%s'",
                        friendly_name,
                        collection_id,
                    )
                    return collection_id, friendly_name

            # Collection not found - fallback to root collection
            root_collection_id = self._settings.PURVIEW_ACCOUNT_NAME
            logger.warning(
                "Collection '%s' not found in Purview. Falling back to root collection '%s'",
                friendly_name,
                root_collection_id,
            )
            return root_collection_id, f"{root_collection_id} (root)"

        except ClientAuthenticationError as e:
            logger.error("Purview authentication failed while listing collections: %s", e)
            raise PurviewAuthenticationError(f"Failed to authenticate with Purview: {e}") from e

        except ServiceRequestError as e:
            logger.error("Failed to connect to Purview while listing collections: %s", e)
            raise PurviewConnectionError(f"Failed to connect to Purview API: {e}") from e

        except Exception as e:
            logger.error("Unexpected error while listing collections: %s", e)
            raise PurviewConnectionError(f"Failed to list Purview collections: {e}") from e

    def create_or_update_entity(
        self,
        entity_payload: dict,
        collection_name: str,
        collection_id: str,
    ) -> dict:
        """
        Create or update an entity in Purview catalog.

        Uses the official Azure Purview SDK to send the entity to the
        catalog API. The SDK handles authentication and request formatting.

        API Endpoint:
            POST {endpoint}/datamap/api/atlas/v2/entity?collectionId={collectionId}
            https://learn.microsoft.com/en-us/rest/api/purview/datamapdataplane/entity/create-or-update

        Request Body:
            {"entities": [entity1, entity2, ...]}

        Args:
            entity_payload: Entity payload from PurviewTableEntity.to_json().
            collection_name: Purview collection friendly name (for logging).
            collection_id: Purview collection ID (passed as query parameter).

        Returns:
            Response dict from Purview API containing guidAssignments and mutatedEntities.

        Raises:
            PurviewAuthenticationError: If authentication fails.
            PurviewConnectionError: If connection to Purview fails.
            PurviewCollectionNotFoundError: If collection doesn't exist.
            PurviewEntityOperationError: If entity operation fails.
        """
        logger.debug(
            "Creating/updating entity in Purview collection '%s' with collection ID '%s'",
            collection_name,
            collection_id,
        )

        try:
            # Pass collection_id via params dict - SDK unpacks kwargs to query params
            response = self._client.entity.create_or_update_entities(
                entities=entity_payload,
                **{"params": {"collectionId": collection_id}},
            )
            logger.debug("Entities created/updated successfully in Purview")
            return response

        except ClientAuthenticationError as e:
            logger.error("Purview authentication failed: %s", e)
            raise PurviewAuthenticationError(f"Failed to authenticate with Purview: {e}") from e

        except ServiceRequestError as e:
            logger.error("Failed to connect to Purview: %s", e)
            raise PurviewConnectionError(f"Failed to connect to Purview API: {e}") from e

        except HttpResponseError as e:
            logger.error("Purview API error (status %s): %s", e.status_code, e)

            if e.status_code in (401, 403):
                raise PurviewAuthenticationError(f"Access denied to Purview: {e}") from e

            if e.status_code == 404:
                error_message = str(e).lower()
                if "collection" in error_message:
                    raise PurviewCollectionNotFoundError(f"Purview collection not found: {collection_name}") from e

            raise PurviewEntityOperationError(f"Purview entity operation failed: {e}") from e

        except Exception as e:
            logger.error("Unexpected error in Purview API call: %s", e)
            raise PurviewEntityOperationError(f"Unexpected error during Purview operation: {e}") from e
