"""
Publish handler - Orchestrates contract publishing to Purview.

Coordinates loading, mapping, and publishing contracts to Microsoft Purview.

Example:
    >>> from databricks_contracts.handlers import PublishHandler
    >>> from databricks_contracts.models.inputs import PublishInput
    >>>
    >>> handler = PublishHandler.create()
    >>> result = handler.handle(PublishInput(contract_name="orders", environment="prod"))
"""

from databricks_contracts.adapters.purview import (
    DryRunPurviewClient,
    PurviewCatalogApiClient,
)
from databricks_contracts.config.logger import get_logger
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
from databricks_contracts.models.inputs import PublishInput
from databricks_contracts.models.results import PublishResult
from databricks_contracts.services.contracts import ContractLoaderService
from databricks_contracts.services.git import ChangeDetectorService
from databricks_contracts.services.purview import ContractToPurviewMapper, PurviewPublisherService

logger = get_logger(__name__)


class PublishHandler:
    """
    Handler for publishing contracts to Microsoft Purview.

    Orchestrates the full publish workflow:
    1. Load contract from YAML
    2. Map contract to Purview entity
    3. Publish entity to Purview catalog

    All exceptions are caught and converted to PublishResult.
    This handler never raises exceptions - it always returns a result.

    Attributes:
        contract_loader: Service for loading contracts from YAML.
        purview_publisher: Service for publishing to Purview.

    Example:
        >>> # Production usage
        >>> handler = PublishHandler.create(environment="prod")
        >>> result = handler.handle(PublishInput(contract_name="orders"))
        >>>
        >>> if result.success:
        ...     print(f"Published to: {result.purview_qualified_name}")
        ... else:
        ...     print(f"Failed: {result.error}")
        >>>
        >>> # Dry run
        >>> handler = PublishHandler.create(dry_run=True)
        >>> result = handler.handle(PublishInput(contract_name="orders"))
    """

    def __init__(
        self,
        contract_loader: ContractLoaderService,
        purview_publisher: PurviewPublisherService,
        change_detector: ChangeDetectorService,
    ) -> None:
        """
        Initialize the publish handler.

        Args:
            contract_loader: Service for loading contracts.
            purview_publisher: Service for publishing to Purview.
            change_detector: Service for detecting modified contracts.

        Example:
            >>> handler = PublishHandler(loader, publisher, change_detector)
        """
        self._contract_loader = contract_loader
        self._purview_publisher = purview_publisher
        self._change_detector = change_detector

    @classmethod
    def create(
        cls,
        environment: str = "dev",
        dry_run: bool = False,
    ) -> "PublishHandler":
        """
        Create handler with default dependencies.

        Factory method for production usage. Creates all dependencies
        with appropriate configuration.

        Args:
            environment: Target environment (dev, prod).
            dry_run: If True, use DryRunPurviewClient instead of real API.

        Returns:
            Configured PublishHandler instance.

        Example:
            >>> handler = PublishHandler.create(environment="prod")
            >>> handler = PublishHandler.create(dry_run=True)
        """
        contract_loader = ContractLoaderService()
        contract_to_purview_mapper = ContractToPurviewMapper()

        # Select client based on dry_run flag
        if dry_run:
            purview_client = DryRunPurviewClient()
        else:
            purview_client = PurviewCatalogApiClient()

        purview_publisher = PurviewPublisherService(
            contract_to_purview_mapper=contract_to_purview_mapper,
            purview_client=purview_client,
        )

        change_detector = ChangeDetectorService.create()

        return cls(contract_loader, purview_publisher, change_detector)

    def handle(self, input_data: PublishInput) -> PublishResult:
        """
        Handle contract publishing to Purview.

        Main entry point for the handler. Loads contract, maps to Purview
        entity, and publishes to Purview catalog.

        This method catches all exceptions and converts them to PublishResult.
        It never raises - always returns a result indicating success or failure.

        Args:
            input_data: Input DTO with contract name and environment.

        Returns:
            PublishResult with outcome and Purview entity details.

        Example:
            >>> input_data = PublishInput(contract_name="orders", environment="prod")
            >>> result = handler.handle(input_data)
            >>>
            >>> if result.success:
            ...     print(f"Published to: {result.purview_qualified_name}")
            ... else:
            ...     print(f"Error: {result.error}")
        """
        contract_name = input_data.contract_name

        logger.info("📤 Publishing contract to Purview: %s", contract_name)

        try:
            # 1. Load contract from YAML
            contract = self._contract_loader.load(contract_name)
            logger.info("✅ Loaded contract: %s v%s", contract.name, contract.version)

            # 2. Publish to Purview (includes mapping)
            result = self._purview_publisher.publish_contract_to_purview(contract)
            logger.info(
                "✅ Successfully published contract '%s' to Purview",
                contract_name,
            )

            return result

        # === CONTRACT ERRORS ===
        except ContractNotFoundError:
            logger.error("❌ Contract not found: %s", contract_name)
            return PublishResult(
                contract_name=contract_name,
                success=False,
                error=f"Contract not found: {contract_name}",
            )

        except ContractParseError as e:
            logger.error("❌ Failed to parse contract '%s': %s", contract_name, e)
            return PublishResult(
                contract_name=contract_name,
                success=False,
                error=f"Failed to parse contract: {e}",
            )

        except ContractValidationError as e:
            logger.error("❌ Contract validation failed '%s': %s", contract_name, e)
            return PublishResult(
                contract_name=contract_name,
                success=False,
                error=f"Contract validation failed: {e}",
            )

        # === PURVIEW MAPPING ERRORS ===
        except PurviewContractMappingError as e:
            logger.error("❌ Failed to map contract '%s' to Purview: %s", contract_name, e)
            return PublishResult(
                contract_name=contract_name,
                success=False,
                error=f"Mapping failed: {e}",
            )

        # === PURVIEW API ERRORS ===
        except PurviewAuthenticationError as e:
            logger.error("❌ Purview authentication failed: %s", e)
            return PublishResult(
                contract_name=contract_name,
                success=False,
                error=f"Purview authentication failed: {e}",
            )

        except PurviewConnectionError as e:
            logger.error("❌ Failed to connect to Purview: %s", e)
            return PublishResult(
                contract_name=contract_name,
                success=False,
                error=f"Connection to Purview failed: {e}",
            )

        except PurviewCollectionNotFoundError as e:
            logger.error("❌ Purview collection not found: %s", e)
            return PublishResult(
                contract_name=contract_name,
                success=False,
                error=str(e),
            )

        except PurviewEntityOperationError as e:
            logger.error("❌ Purview entity operation failed: %s", e)
            return PublishResult(
                contract_name=contract_name,
                success=False,
                error=f"Purview operation failed: {e}",
            )

        except PurviewError as e:
            logger.error("❌ Purview error: %s", e)
            return PublishResult(
                contract_name=contract_name,
                success=False,
                error=str(e),
            )

        # === UNEXPECTED ERRORS ===
        except Exception as e:
            logger.error(
                "❌ Unexpected error publishing contract '%s': %s",
                contract_name,
                e,
            )
            return PublishResult(
                contract_name=contract_name,
                success=False,
                error=f"Unexpected error: {e}",
            )

    def handle_modified(
        self,
        base_ref: str = "HEAD~1",
        head_ref: str = "HEAD",
        environment: str = "dev",
    ) -> list[PublishResult]:
        """
        Publish modified contracts to Purview.

        Detects contracts modified in Git and publishes them to Purview.

        Args:
            base_ref: Git base reference for diff.
            head_ref: Git head reference for diff.
            environment: Target environment (dev, prod).

        Returns:
            List of PublishResult for each modified contract.

        Example:
            >>> results = handler.handle_modified(base_ref="origin/main")
            >>> for result in results:
            ...     print(f"{result.contract_name}: {result.success}")
        """
        logger.info("🔍 Detecting modified contracts...")
        contracts = self._change_detector.get_modified_contracts(base_ref, head_ref)
        logger.info("📋 Found %d modified contract(s)", len(contracts))

        if not contracts:
            logger.info("No modified contracts found")
            return []

        logger.info("📤 Publishing %d contract(s) to Purview...", len(contracts))

        results = []
        for contract_name in contracts:
            input_data = PublishInput(contract_name=contract_name, environment=environment)
            result = self.handle(input_data)
            results.append(result)

        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count
        logger.info("✅ Published: %d, ❌ Failed: %d", success_count, failed_count)

        return results

    def handle_all(self, environment: str = "dev") -> list[PublishResult]:
        """
        Publish all contracts to Purview.

        Publishes all contracts in the contracts directory to Purview.

        Args:
            environment: Target environment (dev, prod).

        Returns:
            List of PublishResult for each contract.

        Example:
            >>> results = handler.handle_all(environment="prod")
        """
        logger.info("🔍 Loading all contracts...")
        contracts = self._contract_loader.list_contracts()

        if not contracts:
            logger.info("No contracts found")
            return []

        logger.info("📤 Publishing %d contract(s) to Purview...", len(contracts))

        results = []
        for contract_name in contracts:
            input_data = PublishInput(contract_name=contract_name, environment=environment)
            result = self.handle(input_data)
            results.append(result)

        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count
        logger.info("✅ Published: %d, ❌ Failed: %d", success_count, failed_count)

        return results
