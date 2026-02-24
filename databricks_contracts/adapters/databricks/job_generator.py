"""
Job generator for Databricks Asset Bundles.

Creates Databricks job configurations from contract files using DAB Python support.

Example:
    >>> from databricks.bundles.core import Bundle, Resources
    >>> from databricks_contracts.adapters.databricks import ContractJobGenerator
    >>>
    >>> def load_resources(bundle: Bundle) -> Resources:
    ...     generator = ContractJobGenerator(bundle)
    ...     return generator.create_resources()
"""

from databricks.bundles.core import Bundle
from databricks.bundles.jobs import Job

from databricks_contracts.config.constants import BundleDefaults
from databricks_contracts.services.paths import PathResolverService


class ContractJobGenerator:
    """
    Generates Databricks jobs for data contracts.

    Creates DAB job configurations for each contract YAML file found.
    Each job applies one contract to Unity Catalog.

    Attributes:
        bundle: DAB Bundle context.
        contracts_path: Resolved path to contracts directory.
        script_path: Path to the Python script that applies contracts.

    Example:
        >>> # In resources/__init__.py
        >>> from databricks.bundles.core import Bundle, Resources
        >>> from databricks_contracts.adapters.databricks import ContractJobGenerator
        >>>
        >>> def load_resources(bundle: Bundle) -> Resources:
        ...     generator = ContractJobGenerator(bundle)
        ...     return generator.create_resources()
        >>>
        >>> # This creates one job per contract file
    """

    def __init__(self, bundle: Bundle) -> None:
        """
        Initialize the job generator.

        Args:
            bundle: DAB Bundle context from Databricks.

        Example:
            >>> generator = ContractJobGenerator(bundle)
        """
        self.bundle = bundle
        self.contracts_path = PathResolverService.create().contracts_path
        self.script_path = BundleDefaults.SCRIPT_PATH

    def get_contract_names(self) -> list[str]:
        """
        Get list of contract names from YAML files.

        Returns:
            List of contract names (without .yaml extension).
            Excludes files starting with underscore.

        Example:
            >>> generator.get_contract_names()
            ["orders_v1", "customers_v1", "transactions_daily"]
        """
        if not self.contracts_path.exists():
            return []

        return [path.stem for path in self.contracts_path.glob("*.yaml") if not path.name.startswith("_")]

    def create_job_for_contract(self, contract_name: str) -> Job:
        """
        Create a Databricks job configuration for a single contract.

        Args:
            contract_name: Name of the contract (without .yaml extension).

        Returns:
            Job configuration for the contract.

        Example:
            >>> job = generator.create_job_for_contract("orders_v1")
            >>> print(job.name)
            "Apply Contract - orders_v1"
        """
        return Job.from_dict(
            {
                "name": BundleDefaults.job_name(contract_name),
                "description": f"Applies data contract '{contract_name}' to Unity Catalog",
                "tasks": [
                    {
                        "task_key": "apply_contract",
                        "spark_python_task": {
                            "python_file": self.script_path,
                            "parameters": [
                                "apply",
                                "contract",
                                contract_name,
                                "--env",
                                "${bundle.target}",
                                "--workflow-sp-id",
                                "${var.WORKFLOW_SP_ID}",
                            ],
                        },
                        "job_cluster_key": "contract_cluster",
                        "libraries": [
                            {
                                "whl": "${var.contracts_wheel}",
                            }
                        ],
                    }
                ],
                "job_clusters": [
                    {
                        "job_cluster_key": "contract_cluster",
                        "new_cluster": {
                            "spark_version": "${var.spark_version}",
                            "node_type_id": "${var.node_type_id}",
                            "num_workers": 0,
                            "data_security_mode": "SINGLE_USER",
                            "spark_conf": {
                                "spark.databricks.cluster.profile": "singleNode",
                                "spark.master": "local[*]",
                            },
                            "custom_tags": {
                                "ResourceClass": "SingleNode",
                            },
                            # "init_scripts": [
                            #     {
                            #         "workspace": {
                            #             "destination": "${var.contracts_init_script_path}",
                            #         }
                            #     }
                            # ],
                        },
                    }
                ],
                "tags": {
                    "contract": contract_name,
                    "managed_by": "databricks-contracts",
                },
                "permissions": [
                    {
                        "group_name": "users",
                        "level": "CAN_VIEW",
                    },
                ],
            }
        )

    def create_jobs(self) -> dict[str, Job]:
        """
        Create jobs for all contracts.

        Returns:
            Dictionary mapping job keys to Job objects.

        Example:
            >>> jobs = generator.create_jobs()
            >>> print(list(jobs.keys()))
            ["apply_orders_v1", "apply_customers_v1"]
        """
        jobs = {}

        for contract_name in self.get_contract_names():
            job_key = f"apply_{contract_name}".replace("-", "_")
            jobs[job_key] = self.create_job_for_contract(contract_name)

        return jobs

    def create_resources(self):
        """
        Create DAB Resources with all contract jobs.

        Returns:
            Resources object with all jobs added.

        Example:
            >>> resources = generator.create_resources()
            >>> # Returns Resources with all contract jobs
        """
        from databricks.bundles.core import Resources

        resources = Resources()

        for job_key, job in self.create_jobs().items():
            resources.add_resource(job_key, job)

        return resources
