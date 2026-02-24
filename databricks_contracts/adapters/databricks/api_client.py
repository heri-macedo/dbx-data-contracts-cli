"""
Databricks Jobs API client adapter.

Provides integration with Databricks Jobs API for triggering and managing jobs.

Example:
    >>> from databricks_contracts.adapters.databricks import DatabricksClient
    >>> client = DatabricksClient()
    >>> job_id = client.find_job_by_name("Apply Contract - orders")
    >>> run_id = client.trigger_job(job_id, "orders_v1")
"""

from functools import cached_property
from typing import Optional

from databricks.sdk import WorkspaceClient

from databricks_contracts.config import get_settings


class DatabricksClient:
    """
    Client adapter for Databricks Jobs API.

    Handles authentication and job operations using the Databricks SDK.
    Uses service principal authentication via environment variables.

    Attributes:
        host: Databricks workspace URL.
        client: Databricks SDK WorkspaceClient instance.

    Example:
        >>> client = DatabricksClient()
        >>>
        >>> # Find job by name pattern
        >>> job_id = client.find_job_by_name("Apply Contract - orders")
        >>>
        >>> # Trigger the job
        >>> run_id = client.trigger_job(job_id, contract_name="orders_v1")
        >>>
        >>> # Get run URL
        >>> url = client.get_run_url(job_id, run_id)
        >>> print(url)
        "https://workspace.databricks.com/#job/123/run/456"
    """

    def __init__(self) -> None:
        """
        Initialize the Databricks client.

        Loads configuration from environment variables via Settings.

        Raises:
            ValueError: If required environment variables are not set.

        Example:
            >>> client = DatabricksClient()
        """
        self._settings = get_settings()

    @property
    def host(self) -> str:
        """
        Get Databricks workspace URL.

        Returns:
            Databricks host URL from settings.

        Raises:
            ValueError: If DATABRICKS_HOST is not configured.

        Example:
            >>> client.host
            "https://myworkspace.databricks.com"
        """
        if not self._settings.DATABRICKS_HOST:
            raise ValueError("DATABRICKS_HOST not configured")
        return self._settings.DATABRICKS_HOST

    @cached_property
    def client(self) -> WorkspaceClient:
        """
        Get the Databricks SDK client (cached on first access).

        Returns:
            Configured WorkspaceClient instance.

        Example:
            >>> ws = client.client
            >>> jobs = ws.jobs.list()
        """
        secret = self._settings.DATABRICKS_CLIENT_SECRET
        client_secret = secret.get_secret_value() if secret else None

        return WorkspaceClient(
            host=self._settings.DATABRICKS_HOST,
            client_id=self._settings.DATABRICKS_CLIENT_ID,
            client_secret=client_secret,
        )

    def find_job_by_name(self, job_name_pattern: str) -> Optional[int]:
        """
        Find a job ID by name pattern.

        Searches all jobs for one containing the pattern (case-insensitive).

        Args:
            job_name_pattern: Pattern to search in job names.

        Returns:
            Job ID if found, None otherwise.

        Example:
            >>> job_id = client.find_job_by_name("Apply Contract - orders")
            >>> if job_id:
            ...     print(f"Found job: {job_id}")
        """
        pattern_lower = job_name_pattern.lower()
        for job in self.client.jobs.list():
            if job.settings and job.settings.name:
                if pattern_lower in job.settings.name.lower():
                    return job.job_id
        return None

    def trigger_job(self, job_id: int, contract_name: str) -> int:
        """
        Trigger a job with contract name parameter.

        Args:
            job_id: Databricks job ID to trigger.
            contract_name: Contract name to pass as job parameter.

        Returns:
            Run ID of the triggered job.

        Raises:
            RuntimeError: If job trigger fails.

        Example:
            >>> run_id = client.trigger_job(123, "orders_v1")
            >>> print(f"Started run: {run_id}")
        """
        run = self.client.jobs.run_now(
            job_id=job_id,
            job_parameters={"contract_name": contract_name},
        )
        if run.run_id is None:
            raise RuntimeError(f"Failed to trigger job {job_id}")
        return run.run_id

    def get_run_url(self, job_id: int, run_id: int) -> str:
        """
        Build URL to access a job run in Databricks UI.

        Args:
            job_id: Databricks job ID.
            run_id: Databricks run ID.

        Returns:
            Full URL to the job run.

        Example:
            >>> url = client.get_run_url(123, 456)
            >>> print(url)
            "https://workspace.databricks.com/#job/123/run/456"
        """
        return f"{self.host.rstrip('/')}/#job/{job_id}/run/{run_id}"
