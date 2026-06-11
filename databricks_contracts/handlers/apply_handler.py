"""
Apply handler - Orchestrates contract application.

Coordinates loading, building, and executing contracts.
Supports both initial table creation and schema evolution.

Example:
    >>> from databricks_contracts.handlers import ApplyHandler
    >>> from databricks_contracts.models.inputs import ApplyInput
    >>>
    >>> handler = ApplyHandler.create()
    >>> result = handler.handle(ApplyInput(contract_name="orders", environment="prod"))
"""

from databricks_contracts.adapters.databricks.executors import BaseExecutor, DryRunExecutor, SparkExecutor
from databricks_contracts.adapters.databricks.sql_client import DatabricksSQLClient
from databricks_contracts.config.logger import get_logger
from databricks_contracts.config.settings import get_settings
from databricks_contracts.exceptions import ExecutionError
from databricks_contracts.models.inputs import ApplyInput
from databricks_contracts.models.results import RunResult
from databricks_contracts.services.contracts import BuilderService, ContractLoaderService, SchemaDifferService
from databricks_contracts.services.databricks.table_inspector import TableInspectorService

logger = get_logger(__name__)


class ApplyHandler:
    """
    Handler for applying contracts to Unity Catalog.

    Orchestrates the full apply workflow:
    1. Load contract from YAML.
    2. Inspect existing table (if any).
    3. If table does NOT exist → CREATE TABLE + SET TAGS + CONSTRAINTS + GRANT.
    4. If table DOES exist → compute diffs → ALTER statements + SET TAGS + CONSTRAINTS + GRANT.
    """

    def __init__(
        self,
        loader: ContractLoaderService,
        builder: BuilderService,
        executor: BaseExecutor,
        inspector: TableInspectorService,
        differ: SchemaDifferService,
    ) -> None:
        self._contract_loader = loader
        self._ddl_builder = builder
        self._ddl_executor = executor
        self._inspector = inspector
        self._differ = differ

    @classmethod
    def create(
        cls,
        environment: str = "dev",
        dry_run: bool = False,
    ) -> "ApplyHandler":
        """Create handler with default dependencies."""
        loader = ContractLoaderService()
        builder = BuilderService(environment=environment)
        ddl_executor: BaseExecutor = DryRunExecutor() if dry_run else SparkExecutor()

        inspector = cls._create_inspector()
        differ = SchemaDifferService()

        return cls(loader, builder, ddl_executor, inspector, differ)

    @staticmethod
    def _create_inspector() -> TableInspectorService:
        """Create the appropriate TableInspectorService based on environment."""
        try:
            spark_executor = SparkExecutor()
            spark_executor.spark  # verify Spark is reachable
            return TableInspectorService(sql_client=None, spark_executor=spark_executor)
        except ExecutionError:
            # No Spark → local dev, try Databricks SDK
            settings = get_settings()
            sql_client = None
            if settings.DATABRICKS_WAREHOUSE_ID:
                sql_client = DatabricksSQLClient(warehouse_id=settings.DATABRICKS_WAREHOUSE_ID)
            return TableInspectorService(sql_client=sql_client, spark_executor=None)

    def handle(self, input: ApplyInput) -> RunResult:
        """Handle contract application with schema evolution support."""
        contract_name = input.contract_name

        logger.info("📄 Loading contract: %s", contract_name)

        try:
            # 1. Load contract
            contract = self._contract_loader.load(contract_name)
            logger.info("✅ Loaded: %s v%s", contract.name, contract.version)

            # 2. Resolve full table name
            full_table_name = self._ddl_builder._resolve_full_name(contract)

            # 3. Inspect existing table
            existing = self._inspector.inspect(full_table_name)

            if existing.exists:
                return self._handle_evolution(contract, existing, full_table_name, contract_name)
            else:
                return self._handle_creation(contract, contract_name)

        except Exception as e:
            logger.error("❌ Failed to apply contract: %s - %s", contract_name, str(e))
            return RunResult(
                contract_name=contract_name,
                success=False,
                error=str(e),
            )

    def _handle_creation(self, contract: object, contract_name: str) -> RunResult:
        """Handle initial table creation (existing flow)."""
        from databricks_contracts.models.contracts.contract import Contract

        assert isinstance(contract, Contract)

        # Build statements
        build_result = self._ddl_builder.build(contract)
        logger.info("🔨 Built %d DDL statement(s)", len(build_result.all_statements))

        # Execute CREATE TABLE (fatal)
        logger.info("🚀 Creating table...")
        create_result = self._ddl_executor.execute(build_result.create_table)
        if not create_result.success:
            return RunResult(
                contract_name=contract_name,
                success=False,
                error=create_result.error,
            )

        # Execute SET TAGS (non-fatal)
        warnings: list[str] = []
        for tag_stmt in build_result.tags:
            tag_result = self._ddl_executor.execute(tag_stmt)
            if not tag_result.success:
                logger.warning("⚠️ Tag skipped: %s — %s", tag_stmt.log_message, tag_result.error)
                warnings.append(f"{tag_stmt.log_message}: {tag_result.error}")

        # Execute CONSTRAINTS (non-fatal)
        for constraint_stmt in build_result.constraints:
            constraint_result = self._ddl_executor.execute(constraint_stmt)
            if not constraint_result.success:
                logger.warning("⚠️ Constraint skipped: %s — %s", constraint_stmt.log_message, constraint_result.error)
                warnings.append(f"{constraint_stmt.log_message}: {constraint_result.error}")

        # Execute GRANT (non-fatal, skipped if not configured)
        if build_result.grant:
            grant_result = self._ddl_executor.execute(build_result.grant)
            if not grant_result.success:
                logger.warning("⚠️ Grant error: %s", grant_result.error)
                warnings.append(f"GRANT: {grant_result.error}")

        if warnings:
            logger.info("✅ Applied contract %s with %d warning(s)", contract_name, len(warnings))
        else:
            logger.info("✅ Successfully applied contract: %s", contract_name)

        return RunResult(
            contract_name=contract_name,
            success=True,
            create_ddl=build_result.create_ddl,
            tags_ddl=build_result.tags_ddl,
            warnings=warnings,
        )

    def _handle_evolution(
        self,
        contract: object,
        existing: object,
        full_table_name: str,
        contract_name: str,
    ) -> RunResult:
        """Handle schema evolution for an existing table."""
        from databricks_contracts.models.contracts.contract import Contract
        from databricks_contracts.services.databricks.table_inspector import ExistingTableSchema

        assert isinstance(contract, Contract)
        assert isinstance(existing, ExistingTableSchema)

        logger.info("🔄 Table exists, computing schema diff...")

        # Compute diffs
        diffs = self._differ.diff(contract, existing)

        if not diffs:
            logger.info("✅ No schema changes detected")

        # Build evolution statements
        evolution_result = self._ddl_builder.build_evolution(contract, diffs, full_table_name)

        warnings: list[str] = list(evolution_result.warnings)

        # Execute ALTER statements (fatal — these are safe changes)
        alter_ddl_list: list[str] = []
        for alter_stmt in evolution_result.alter_statements:
            logger.info("🔄 Executing: %s", alter_stmt.log_message)
            result = self._ddl_executor.execute(alter_stmt)
            if not result.success:
                return RunResult(
                    contract_name=contract_name,
                    success=False,
                    error=result.error,
                    is_evolution=True,
                )
            alter_ddl_list.append(alter_stmt.statement)

        # Execute SET TAGS (non-fatal, idempotent)
        for tag_stmt in evolution_result.tag_statements:
            tag_result = self._ddl_executor.execute(tag_stmt)
            if not tag_result.success:
                logger.warning("⚠️ Tag skipped: %s — %s", tag_stmt.log_message, tag_result.error)
                warnings.append(f"{tag_stmt.log_message}: {tag_result.error}")

        # Execute CONSTRAINTS (non-fatal — may already exist)
        for constraint_stmt in evolution_result.constraint_statements:
            constraint_result = self._ddl_executor.execute(constraint_stmt)
            if not constraint_result.success:
                logger.warning("⚠️ Constraint skipped: %s — %s", constraint_stmt.log_message, constraint_result.error)
                warnings.append(f"{constraint_stmt.log_message}: {constraint_result.error}")

        # Execute GRANT (non-fatal)
        if evolution_result.grant:
            grant_result = self._ddl_executor.execute(evolution_result.grant)
            if not grant_result.success:
                logger.warning("⚠️ Grant error: %s", grant_result.error)
                warnings.append(f"GRANT: {grant_result.error}")

        tags_ddl = "\n".join(t.statement for t in evolution_result.tag_statements)

        if warnings:
            logger.info("✅ Evolved contract %s with %d warning(s)", contract_name, len(warnings))
        else:
            logger.info("✅ Successfully evolved contract: %s", contract_name)

        return RunResult(
            contract_name=contract_name,
            success=True,
            tags_ddl=tags_ddl,
            alter_ddl=alter_ddl_list,
            is_evolution=True,
            warnings=warnings,
        )
