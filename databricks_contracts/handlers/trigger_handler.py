"""
Trigger handler - Orchestrates job triggering.

Triggers Databricks jobs for contracts.

Example:
    >>> from databricks_contracts.handlers import TriggerHandler
    >>> from databricks_contracts.models.inputs import TriggerInput
    >>>
    >>> handler = TriggerHandler.create()
    >>> results = handler.handle(TriggerInput(contracts=["orders", "customers"]))
"""

from databricks_contracts.config.logger import get_logger
from databricks_contracts.models.inputs import TriggerInput
from databricks_contracts.models.results import TriggerResult
from databricks_contracts.services.contracts.loader import ContractLoaderService
from databricks_contracts.services.databricks import TriggerService
from databricks_contracts.services.git import ChangeDetectorService

logger = get_logger(__name__)


class TriggerHandler:
    """
    Handler for triggering Databricks jobs.

    Orchestrates job triggering for contracts, with optional
    detection of modified contracts via Git.

    Attributes:
        trigger_service: Service for triggering jobs.
        change_detector: Service for detecting modified contracts.

    Example:
        >>> # Trigger specific contracts
        >>> handler = TriggerHandler.create()
        >>> results = handler.handle(TriggerInput(contracts=["orders"]))
        >>>
        >>> # Trigger modified contracts
        >>> handler = TriggerHandler.create()
        >>> modified = handler.get_modified_contracts(base_ref="origin/main")
        >>> results = handler.handle(TriggerInput(contracts=modified))
    """

    def __init__(
        self,
        trigger_service: TriggerService,
        change_detector: ChangeDetectorService,
        contracts_loader_service: ContractLoaderService,
    ) -> None:
        """
        Initialize the trigger handler.

        Args:
            trigger_service: Service for triggering jobs.
            change_detector: Service for detecting modified contracts.
            contracts_loader_service: Service for loading contracts.
        Example:
            >>> handler = TriggerHandler(trigger_service, change_detector, contracts_loader_service)
        """
        self._trigger = trigger_service
        self._change_detector = change_detector
        self._contracts_loader_service = contracts_loader_service

    @classmethod
    def create(cls, dry_run: bool = False) -> "TriggerHandler":
        """
        Create handler with default dependencies.

        Args:
            dry_run: If True, don't actually trigger jobs.

        Returns:
            Configured TriggerHandler instance.

        Example:
            >>> handler = TriggerHandler.create()
            >>> handler = TriggerHandler.create(dry_run=True)
        """
        trigger_service = TriggerService.create(dry_run=dry_run)
        change_detector = ChangeDetectorService.create()
        contracts_loader_service = ContractLoaderService()
        return cls(trigger_service, change_detector, contracts_loader_service)

    def handle(self, input: TriggerInput) -> list[TriggerResult]:
        """
        Handle job triggering.

        Triggers Databricks jobs for the specified contracts.

        Args:
            input: Input DTO with contract names.

        Returns:
            List of TriggerResult for each contract.

        Example:
            >>> input = TriggerInput(contracts=["orders", "customers"])
            >>> results = handler.handle(input)
            >>>
            >>> for result in results:
            ...     if result.success:
            ...         print(f"✅ {result.contract_name}: {result.run_url}")
            ...     else:
            ...         print(f"❌ {result.contract_name}: {result.error}")
        """
        contracts = input.contracts

        if not contracts:
            logger.info("No contracts to trigger")
            return []

        logger.info("🚀 Triggering jobs for %d contract(s)...", len(contracts))

        results = self._trigger.trigger_batch(contracts)

        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count

        logger.info("✅ Triggered: %d, ❌ Failed: %d", success_count, failed_count)

        return results

    def handle_modified(
        self,
        base_ref: str = "HEAD~1",
        head_ref: str = "HEAD",
    ) -> list[TriggerResult]:
        """
        Trigger jobs for modified contracts.

        Convenience method that combines detection and triggering.

        Args:
            base_ref: Git base reference for diff.
            head_ref: Git head reference for diff.

        Returns:
            List of TriggerResult for each modified contract.

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

        return self.handle(TriggerInput(contracts=contracts, base_ref=base_ref))

    def handle_all(self) -> list[TriggerResult]:
        """
        Trigger jobs for all contracts.

        Triggers jobs for all contracts in the contracts directory.

        Returns:
            List of TriggerResult for each contract.
        """
        logger.info("🔍 Loading all contracts...")
        contracts = self._contracts_loader_service.list_contracts()

        if not contracts:
            logger.info("No contracts found")
            return []

        logger.info("🚀 Triggering jobs for %d contract(s)...", len(contracts))

        return self.handle(TriggerInput(contracts=contracts))
