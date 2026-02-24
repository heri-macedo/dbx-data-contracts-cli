"""
Apply handler - Orchestrates contract application.

Coordinates loading, building, and executing contracts.

Example:
    >>> from databricks_contracts.handlers import ApplyHandler
    >>> from databricks_contracts.models.inputs import ApplyInput
    >>>
    >>> handler = ApplyHandler.create()
    >>> result = handler.handle(ApplyInput(contract_name="orders", environment="prod"))
"""

from databricks_contracts.adapters.databricks.executors import BaseExecutor, DryRunExecutor, SparkExecutor
from databricks_contracts.config.logger import get_logger
from databricks_contracts.models.inputs import ApplyInput
from databricks_contracts.models.results import RunResult
from databricks_contracts.services.contracts import BuilderService, ContractLoaderService

logger = get_logger(__name__)


class ApplyHandler:
    """
    Handler for applying contracts to Unity Catalog.

    Orchestrates the full apply workflow:
    1. Load contract from YAML.
    2. Build DDL statements (one per tag).
    3. Execute CREATE TABLE (**fatal** on failure).
    4. Execute SET TAGS individually (**non-fatal** — failures become warnings).
    5. Execute GRANT (**non-fatal** — failure becomes a warning).

    Only a CREATE TABLE failure causes ``success=False``.  Tag and grant
    failures are collected in ``RunResult.warnings`` so the table is still
    created even when the executing principal lacks certain tag-policy
    permissions.

    Example:
        >>> handler = ApplyHandler.create(environment="prod")
        >>> result = handler.handle(ApplyInput(contract_name="orders"))
        >>> if result.success:
        ...     print(f"Applied: {result.contract_name}")
        ...     for w in result.warnings:
        ...         print(f"  ⚠ {w}")
        ... else:
        ...     print(f"Failed: {result.error}")
    """

    def __init__(
        self,
        loader: ContractLoaderService,
        builder: BuilderService,
        executor: BaseExecutor,
    ) -> None:
        """
        Initialize the apply handler.

        Args:
            loader: Service for loading contracts.
            builder: Service for building DDL statements.
            executor: Executor for running DDL (Spark or DryRun).

        Example:
            >>> handler = ApplyHandler(loader, builder, executor)
        """
        self._contract_loader = loader
        self._ddl_builder = builder
        self._ddl_executor = executor

    @classmethod
    def create(
        cls,
        environment: str = "dev",
        dry_run: bool = False,
    ) -> "ApplyHandler":
        """
        Create handler with default dependencies.

        Factory method for production usage. Creates all dependencies
        with appropriate configuration.

        Args:
            environment: Target environment (dev, prod).
            dry_run: If True, use DryRunExecutor instead of Spark.

        Returns:
            Configured ApplyHandler instance.

        Example:
            >>> # Production
            >>> handler = ApplyHandler.create(environment="prod")
            >>>
            >>> # Dry run
            >>> handler = ApplyHandler.create(dry_run=True)
        """
        loader = ContractLoaderService()
        builder = BuilderService(environment=environment)
        ddl_executor: BaseExecutor = DryRunExecutor() if dry_run else SparkExecutor()

        return cls(loader, builder, ddl_executor)

    def handle(self, input: ApplyInput) -> RunResult:
        """
        Handle contract application.

        Execution strategy:
        - CREATE TABLE is **fatal** — failure aborts with ``success=False``.
        - SET TAGS and GRANT are **non-fatal** — failures are collected
          in ``RunResult.warnings`` and the result is still ``success=True``.

        Args:
            input: Input DTO with contract name and environment.

        Returns:
            RunResult with outcome, generated DDL, and any warnings.

        Example:
            >>> result = handler.handle(ApplyInput(contract_name="orders"))
            >>> if result.success:
            ...     print(f"Applied ({result.statements_count} stmts)")
            ...     for w in result.warnings:
            ...         print(f"  ⚠ {w}")
        """
        contract_name = input.contract_name

        logger.info("📄 Loading contract: %s", contract_name)

        try:
            # 1. Load contract
            contract = self._contract_loader.load(contract_name)
            logger.info("✅ Loaded: %s v%s", contract.name, contract.version)

            # 2. Build statements
            build_result = self._ddl_builder.build(contract)
            logger.info("🔨 Built %d DDL statement(s)", len(build_result.all_statements))

            # 3. Execute CREATE TABLE (fatal)
            logger.info("🚀 Creating table...")
            create_result = self._ddl_executor.execute(build_result.create_table)
            if not create_result.success:
                return RunResult(
                    contract_name=contract_name,
                    success=False,
                    error=create_result.error,
                )

            # 4. Execute SET TAGS (non-fatal — failures become warnings)
            warnings: list[str] = []
            for tag_stmt in build_result.tags:
                tag_result = self._ddl_executor.execute(tag_stmt)
                if not tag_result.success:
                    logger.warning("⚠️ Tag skipped: %s — %s", tag_stmt.log_message, tag_result.error)
                    warnings.append(f"{tag_stmt.log_message}: {tag_result.error}")

            # 5. Execute GRANT (non-fatal)
            grant_result = self._ddl_executor.execute(build_result.grant)
            if not grant_result.success:
                logger.warning("⚠️ Grant error: %s", grant_result.error)
                warnings.append(f"GRANT: {grant_result.error}")

            if warnings:
                logger.info(
                    "✅ Applied contract %s with %d warning(s)",
                    contract_name,
                    len(warnings),
                )
            else:
                logger.info("✅ Successfully applied contract: %s", contract_name)

            return RunResult(
                contract_name=contract_name,
                success=True,
                create_ddl=build_result.create_ddl,
                tags_ddl=build_result.tags_ddl,
                warnings=warnings,
            )

        except Exception as e:
            logger.error("❌ Failed to apply contract: %s - %s", contract_name, str(e))
            return RunResult(
                contract_name=contract_name,
                success=False,
                error=str(e),
            )
