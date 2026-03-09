"""
Builder service for DDL generation.

Builds DDL statements from contracts.

Example:
    >>> from databricks_contracts.services.contracts import BuilderService
    >>> builder = BuilderService(environment="prod")
    >>> statements = builder.build(contract)
"""

import os
from typing import Optional

from databricks_contracts.config.constants import DDLKeywords
from databricks_contracts.config.project_config_model import ProjectConfig, load_project_config
from databricks_contracts.models.contracts import Column, Contract
from databricks_contracts.models.results import StatementBuildResult
from databricks_contracts.models.statements import CreateTableStatement, GrantStatement, TagStatement


class BuilderService:
    """
    Service for building DDL statements from contracts.

    Generates CREATE TABLE and SET TAGS statements for Unity Catalog.

    Attributes:
        environment: Target environment (dev, prod).
        project_config: Project configuration for catalog/schema resolution.

    Example:
        >>> builder = BuilderService(environment="prod")
        >>>
        >>> # Build statements for a contract
        >>> statements = builder.build(contract)
        >>>
        >>> # Statements include CREATE TABLE + SET TAGS
        >>> for stmt in statements:
        ...     print(stmt.log_message)
    """

    def __init__(
        self,
        environment: str = "dev",
        project_config: Optional[ProjectConfig] = None,
    ) -> None:
        """
        Initialize the builder service.

        Args:
            environment: Target environment (dev, prod).
            project_config: Project configuration. If None, loads from file.

        Example:
            >>> builder = BuilderService(environment="prod")
            >>> builder = BuilderService(environment="dev", project_config=config)
        """
        self._environment = environment
        self._project_config = project_config or load_project_config()

    def build(self, contract: Contract) -> StatementBuildResult:
        """
        Build all DDL statements for a contract.

        Generates:
        - 1 × CREATE TABLE statement
        - N × SET TAGS statements (one per tag, table-level and column-level)
        - 1 × GRANT statement (if ``WORKFLOW_SP_ID`` is set)

        Each tag is emitted as an individual statement so that a failure
        on one tag does not block the others.

        Args:
            contract: Contract model to build DDL from.

        Returns:
            StatementBuildResult with structured access to statements.

        Example:
            >>> result = builder.build(contract)
            >>> print(result.create_ddl)
            >>> print(len(result.tags))  # one TagStatement per tag
        """
        catalog = self._project_config.get_catalog(self._environment)
        schema = self._project_config.schema_name
        full_name = f"`{catalog}`.`{schema}`.`{contract.table.name}`"

        # CREATE TABLE
        create_stmt = self._build_create_table(contract, catalog, schema)

        # SET TAGS
        tag_stmts = self._build_tags(contract, catalog, schema)

        # GRANT (if workflow_sp_id is configured)
        grant_stmt = self._build_grant(full_name)

        return StatementBuildResult(create_table=create_stmt, tags=tag_stmts, grant=grant_stmt)

    def _build_create_table(
        self,
        contract: Contract,
        catalog: str,
        schema: str,
    ) -> CreateTableStatement:
        """
        Build CREATE TABLE statement.

        Args:
            contract: Contract model.
            catalog: Resolved catalog name.
            schema: Resolved schema name.

        Returns:
            CreateTableStatement with DDL.
        """
        table = contract.table
        full_name = f"`{catalog}`.`{schema}`.`{table.name}`"

        # Build column definitions
        columns_ddl = ",\n".join(self._column_definition(col) for col in table.columns)

        # Build CREATE TABLE
        ddl_parts = [
            f"{DDLKeywords.CREATE_TABLE} {DDLKeywords.IF_NOT_EXISTS} {full_name} (",
            columns_ddl,
            ")",
            DDLKeywords.USING_DELTA,
        ]

        # Add PARTITIONED BY if specified
        if table.partitioned_by:
            partition_cols = ", ".join(f"`{col}`" for col in table.partitioned_by)
            ddl_parts.append(f"{DDLKeywords.PARTITIONED_BY} ({partition_cols})")

        # Add COMMENT if present
        if table.description:
            escaped = self._escape_string(table.description)
            ddl_parts.append(f"{DDLKeywords.COMMENT} '{escaped}'")

        # Add TBLPROPERTIES
        properties = {
            "refresh_frequency": table.refresh_frequency.value,
            "retention_days": str(table.retention_days),
        }
        props_sql = ", ".join(f"'{k}' = '{v}'" for k, v in properties.items())
        ddl_parts.append(f"{DDLKeywords.TBLPROPERTIES} ({props_sql})")

        ddl = "\n".join(ddl_parts) + ";"

        return CreateTableStatement(full_table_name=full_name, ddl=ddl)

    def _column_definition(self, column: Column) -> str:
        """Build a single column definition."""
        parts = [f"  `{column.name}`", column.type.upper()]

        if not column.nullable:
            parts.append(DDLKeywords.NOT_NULL)

        if column.description:
            escaped = self._escape_string(column.description)
            parts.append(f"{DDLKeywords.COMMENT} '{escaped}'")

        return " ".join(parts)

    def _build_tags(
        self,
        contract: Contract,
        catalog: str,
        schema: str,
    ) -> list[TagStatement]:
        """
        Build SET TAGS statements — **one statement per tag**.

        Each tag gets its own ``ALTER TABLE … SET TAGS`` so that a
        permission error on one tag (e.g. a restricted tag policy) does
        not prevent the remaining tags from being applied.

        Args:
            contract: Contract model.
            catalog: Resolved catalog name.
            schema: Resolved schema name.

        Returns:
            List of TagStatement (one per tag, for both table and columns).
        """
        full_name = f"`{catalog}`.`{schema}`.`{contract.table.name}`"
        statements: list[TagStatement] = []

        # Table-level tags (one statement per tag)
        table_tags = self._build_table_tags(contract)
        for key, value in table_tags.items():
            statements.append(TagStatement(target="table", tags={key: value}, full_table_name=full_name))

        # Column-level tags (one statement per tag)
        for column in contract.table.columns:
            if column.tags:
                col_tags = column.tags.to_dict()
                for key, value in col_tags.items():
                    statements.append(TagStatement(target=column.name, tags={key: value}, full_table_name=full_name))

        return statements

    def _build_table_tags(self, contract: Contract) -> dict[str, str]:
        """Build table-level tags dictionary."""
        tags: dict[str, str] = {
            "portfolio": contract.ownership.portfolio.value,
            "sub_domain": contract.ownership.sub_domain.value,
        }

        # Add table tags
        tags.update(contract.table.tags.to_dict())

        return tags

    def _build_grant(self, full_table_name: str) -> Optional[GrantStatement]:
        """
        Build GRANT MODIFY statement for the workflow Service Principal.

        Args:
            full_table_name: Fully qualified table name with backticks.

        Returns:
            GrantStatement for the configured SP, or None if SP ID not configured.
        """
        workflow_sp_id = os.environ.get("WORKFLOW_SP_ID")
        if not workflow_sp_id:
            return None
        return GrantStatement(full_table_name=full_table_name, principal=workflow_sp_id)

    @staticmethod
    def _escape_string(value: str) -> str:
        """
        Escape string values for safe inclusion in SQL single-quoted literals.

        Notes:
            - Spark SQL / Databricks SQL string literals are single-quoted.
            - The most portable escape for a single quote is doubling it: ' -> ''.
            - Newlines are normalized to spaces to avoid multi-line SQL.
        """
        return value.replace("'", "''").replace("\n", " ")
