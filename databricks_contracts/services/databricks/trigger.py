"""
Trigger service for Databricks jobs.

Triggers Databricks jobs for contracts.

Example:
    >>> from databricks_contracts.services.databricks import TriggerService
    >>> service = TriggerService.create()
    >>> result = service.trigger("orders_v1")
"""

from databricks_contracts.adapters.databricks.api_client import DatabricksClient
from databricks_contracts.config.constants import BundleDefaults
from databricks_contracts.models.results import TriggerResult


class TriggerService:
    """
    Service for triggering Databricks jobs.

    Finds and triggers jobs for contracts, handling job name resolution.

    Attributes:
        client: Databricks API client.
        dry_run: If True, don't actually trigger jobs.

    Example:
        >>> # Create service
        >>> service = TriggerService.create()
        >>>
        >>> # Trigger a single contract
        >>> result = service.trigger("orders_v1")
        >>> if result.success:
        ...     print(f"Run URL: {result.run_url}")
        >>>
        >>> # Trigger multiple contracts
        >>> results = service.trigger_batch(["orders_v1", "customers_v1"])
    """

    def __init__(
        self,
        client: DatabricksClient,
        dry_run: bool = False,
    ) -> None:
        """
        Initialize the trigger service.

        Args:
            client: Databricks API client.
            dry_run: If True, don't actually trigger jobs.

        Example:
            >>> client = DatabricksClient()
            >>> service = TriggerService(client)
            >>> service = TriggerService(client, dry_run=True)
        """
        self._client = client
        self._dry_run = dry_run

    @classmethod
    def create(cls, dry_run: bool = False) -> "TriggerService":
        """
        Create service with default dependencies.

        Args:
            dry_run: If True, don't actually trigger jobs.

        Returns:
            TriggerService with Databricks client.

        Example:
            >>> service = TriggerService.create()
            >>> service = TriggerService.create(dry_run=True)
        """
        client = DatabricksClient()
        return cls(client, dry_run)

    def trigger(self, contract_name: str) -> TriggerResult:
        """
        Trigger job for a single contract.

        Args:
            contract_name: Name of the contract.

        Returns:
            TriggerResult with outcome.

        Example:
            >>> result = service.trigger("orders_v1")
            >>> if result.success:
            ...     print(f"Started: {result.run_id}")
            ...     print(f"URL: {result.run_url}")
            ... else:
            ...     print(f"Failed: {result.error}")
        """
        job_name = BundleDefaults.job_name(contract_name)

        if self._dry_run:
            return TriggerResult(
                contract_name=contract_name,
                success=True,
                error="[DRY RUN] Would trigger job",
            )

        try:
            job_id = self._client.find_job_by_name(job_name)

            if not job_id:
                return TriggerResult(
                    contract_name=contract_name,
                    success=False,
                    error=f"Job not found: {job_name}",
                )

            run_id = self._client.trigger_job(job_id, contract_name)
            run_url = self._client.get_run_url(job_id, run_id)

            return TriggerResult(
                contract_name=contract_name,
                success=True,
                run_id=run_id,
                run_url=run_url,
            )
        except Exception as e:
            return TriggerResult(
                contract_name=contract_name,
                success=False,
                error=str(e),
            )

    def trigger_batch(self, contract_names: list[str]) -> list[TriggerResult]:
        """
        Trigger jobs for multiple contracts.

        Args:
            contract_names: List of contract names.

        Returns:
            List of TriggerResult for each contract.

        Example:
            >>> results = service.trigger_batch(["orders", "customers"])
            >>> success = sum(1 for r in results if r.success)
            >>> print(f"{success}/{len(results)} succeeded")
        """
        return [self.trigger(name) for name in contract_names]
