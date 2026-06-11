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
from databricks_contracts.models.results.build_result import EvolutionBuildResult, StatementBuildResult
from databricks_contracts.models.statements import (
    AddColumnsStatement,
    AlterColumnCommentStatement,
    AlterColumnNullabilityStatement,
    AlterTableCommentStatement,
    AlterTablePropertiesStatement,
    BaseStatement,
    CreateTableStatement,
    GrantStatement,
    TagStatement,
)
from databricks_contracts.models.statements.constraint import AddConstraintStatement
from databricks_contracts.services.contracts.schema_differ import DiffType, SchemaDiff
from databricks_contracts.utils.sql import escape_sql_literal


class BuilderService:
    """
    Service for building DDL statements from contracts.

    Generates CREATE TABLE, SET TAGS, CHECK constraints, and ALTER statements
    for Unity Catalog.
    """

    def __init__(
        self,
        environment: str = "dev",
        project_config: Optional[ProjectConfig] = None,
    ) -> None:
        self._environment = environment
        self._project_config = project_config or load_project_config()

    def build(self, contract: Contract) -> StatementBuildResult:
        """Build all DDL statements for initial table creation."""
        catalog = self._project_config.get_catalog(self._environment)
        schema = self._project_config.schema_name
        full_name = f"`{catalog}`.`{schema}`.`{contract.table.name}`"

        create_stmt = self._build_create_table(contract, catalog, schema)
        tag_stmts = self._build_tags(contract, catalog, schema)
        constraint_stmts = self._build_constraints(contract, full_name)
        grant_stmt = self._build_grant(full_name)

        return StatementBuildResult(
            create_table=create_stmt,
            tags=tag_stmts,
            constraints=constraint_stmts,
            grant=grant_stmt,
        )

    def build_evolution(
        self,
        contract: Contract,
        diffs: list[SchemaDiff],
        full_table_name: str,
    ) -> EvolutionBuildResult:
        """Build ALTER statements from schema diffs. Unsafe diffs become warnings."""
        alter_stmts: list[BaseStatement] = []
        warnings: list[str] = []

        for d in diffs:
            if not d.is_safe:
                if d.diff_type == DiffType.REMOVE_COLUMN:
                    warnings.append(
                        f"Column `{d.column_name}` exists in table but not in contract — "
                        f"will NOT be dropped automatically"
                    )
                elif d.diff_type == DiffType.MODIFY_COLUMN_TYPE:
                    warnings.append(
                        f"Column `{d.column_name}` type change from {d.current_value} to "
                        f"{d.desired_value} is not a safe widening — skipped"
                    )
                continue

            if d.diff_type == DiffType.ADD_COLUMN:
                col = next((c for c in contract.table.columns if c.name == d.column_name), None)
                if col:
                    alter_stmts.append(
                        AddColumnsStatement(
                            full_table_name=full_table_name,
                            column_name=col.name,
                            column_type=col.type.upper(),
                            nullable=col.nullable,
                            comment=col.description,
                        )
                    )

            elif d.diff_type == DiffType.MODIFY_COLUMN_COMMENT:
                alter_stmts.append(
                    AlterColumnCommentStatement(
                        full_table_name=full_table_name,
                        column_name=d.column_name or "",
                        comment=d.desired_value or "",
                    )
                )

            elif d.diff_type == DiffType.MODIFY_COLUMN_NULLABILITY:
                set_not_null = d.desired_value == "NOT NULL"
                alter_stmts.append(
                    AlterColumnNullabilityStatement(
                        full_table_name=full_table_name,
                        column_name=d.column_name or "",
                        set_not_null=set_not_null,
                    )
                )

            elif d.diff_type == DiffType.UPDATE_TABLE_COMMENT:
                alter_stmts.append(
                    AlterTableCommentStatement(
                        full_table_name=full_table_name,
                        comment=d.desired_value or "",
                    )
                )

            elif d.diff_type == DiffType.UPDATE_TBLPROPERTIES:
                properties = {
                    "refresh_frequency": contract.table.refresh_frequency.value,
                    "retention_days": str(contract.table.retention_days),
                    "delta.deletedFileRetentionDuration": f"interval {contract.table.retention_days} days",
                    "delta.logRetentionDuration": f"interval {contract.table.retention_days} days",
                }
                alter_stmts.append(
                    AlterTablePropertiesStatement(
                        full_table_name=full_table_name,
                        properties=properties,
                    )
                )

        # Tags are always applied (idempotent)
        catalog = self._project_config.get_catalog(self._environment)
        schema = self._project_config.schema_name
        tag_stmts = self._build_tags(contract, catalog, schema)

        # Constraints
        constraint_stmts = self._build_constraints(contract, full_table_name)

        # Grant
        grant_stmt = self._build_grant(full_table_name)

        return EvolutionBuildResult(
            alter_statements=alter_stmts,
            tag_statements=tag_stmts,
            constraint_statements=constraint_stmts,
            grant=grant_stmt,
            warnings=warnings,
        )

    def _resolve_full_name(self, contract: Contract) -> str:
        """Resolve the fully qualified table name with backticks."""
        catalog = self._project_config.get_catalog(self._environment)
        schema = self._project_config.schema_name
        return f"`{catalog}`.`{schema}`.`{contract.table.name}`"

    def _build_create_table(
        self,
        contract: Contract,
        catalog: str,
        schema: str,
    ) -> CreateTableStatement:
        """Build CREATE TABLE statement."""
        table = contract.table
        full_name = f"`{catalog}`.`{schema}`.`{table.name}`"

        columns_ddl = ",\n".join(self._column_definition(col) for col in table.columns)

        ddl_parts = [
            f"{DDLKeywords.CREATE_TABLE} {DDLKeywords.IF_NOT_EXISTS} {full_name} (",
            columns_ddl,
            ")",
            DDLKeywords.USING_DELTA,
        ]

        if table.partitioned_by:
            partition_cols = ", ".join(f"`{col}`" for col in table.partitioned_by)
            ddl_parts.append(f"{DDLKeywords.PARTITIONED_BY} ({partition_cols})")

        if table.description:
            escaped = self._escape_string(table.description)
            ddl_parts.append(f"{DDLKeywords.COMMENT} '{escaped}'")

        properties = {
            "refresh_frequency": table.refresh_frequency.value,
            "retention_days": str(table.retention_days),
            "delta.deletedFileRetentionDuration": f"interval {table.retention_days} days",
            "delta.logRetentionDuration": f"interval {table.retention_days} days",
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
        """Build SET TAGS statements — one statement per tag."""
        full_name = f"`{catalog}`.`{schema}`.`{contract.table.name}`"
        statements: list[TagStatement] = []

        table_tags = self._build_table_tags(contract)
        for key, value in table_tags.items():
            statements.append(TagStatement(target="table", tags={key: value}, full_table_name=full_name))

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
        tags.update(contract.table.tags.to_dict())
        return tags

    def _build_constraints(
        self,
        contract: Contract,
        full_table_name: str,
    ) -> list[AddConstraintStatement]:
        """Build ADD CONSTRAINT statements for columns with check constraints."""
        stmts: list[AddConstraintStatement] = []
        table_name = contract.table.name
        for col in contract.table.columns:
            if col.constraints and col.constraints.check:
                constraint_name = f"chk_{table_name}_{col.name}"
                stmts.append(
                    AddConstraintStatement(
                        full_table_name=full_table_name,
                        constraint_name=constraint_name,
                        check_expression=col.constraints.check,
                    )
                )
        return stmts

    def _build_grant(self, full_table_name: str) -> Optional[GrantStatement]:
        """Build GRANT MODIFY statement for the workflow Service Principal."""
        workflow_sp_id = os.environ.get("WORKFLOW_SP_ID")
        if not workflow_sp_id:
            return None
        return GrantStatement(full_table_name=full_table_name, principal=workflow_sp_id)

    @staticmethod
    def _escape_string(value: str) -> str:
        """Escape string values for safe inclusion in SQL single-quoted literals."""
        return escape_sql_literal(value)
