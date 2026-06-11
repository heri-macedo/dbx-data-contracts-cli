"""Table introspection service for reading existing table schema from Unity Catalog."""

from typing import Any, Optional

from pydantic import BaseModel, Field

from databricks_contracts.adapters.databricks.sql_client import DatabricksSQLClient
from databricks_contracts.config.logger import get_logger
from databricks_contracts.models.results.query_result import QueryResult

logger = get_logger(__name__)


class ExistingColumn(BaseModel):
    """Represents a column as it currently exists in the table."""

    model_config = {"frozen": True}

    name: str
    type: str
    nullable: bool
    comment: Optional[str] = None


class ExistingTableSchema(BaseModel):
    """Represents the current state of a table in Unity Catalog."""

    model_config = {"frozen": True}

    exists: bool
    columns: list[ExistingColumn] = Field(default_factory=list)
    comment: Optional[str] = None
    tblproperties: dict[str, str] = Field(default_factory=dict)


class TableInspectorService:
    """Inspects existing tables in Unity Catalog to determine current schema.

    Uses either a SparkExecutor (in Databricks) or DatabricksSQLClient (locally)
    to query the table. Falls back to exists=False if neither is available.
    """

    def __init__(
        self,
        sql_client: Optional[DatabricksSQLClient] = None,
        spark_executor: Optional[Any] = None,
    ) -> None:
        self._sql_client = sql_client
        self._spark_executor = spark_executor

    def inspect(self, full_table_name: str) -> ExistingTableSchema:
        """Inspect a table and return its current schema.

        Args:
            full_table_name: Fully qualified table name with backticks.

        Returns:
            ExistingTableSchema with current table state, or exists=False if
            table doesn't exist or introspection is unavailable.
        """
        if self._spark_executor:
            return self._inspect_via_spark(full_table_name)
        if self._sql_client:
            return self._inspect_via_sdk(full_table_name)
        return ExistingTableSchema(exists=False)

    def _inspect_via_spark(self, full_table_name: str) -> ExistingTableSchema:
        """Inspect table using Spark SQL."""
        try:
            spark = self._spark_executor.spark

            # Check if table exists
            try:
                desc_rows = spark.sql(f"DESCRIBE TABLE EXTENDED {full_table_name}").collect()
            except Exception:
                return ExistingTableSchema(exists=False)

            columns = self._parse_describe_rows(
                [{"col_name": r["col_name"], "data_type": r["data_type"], "comment": r["comment"]} for r in desc_rows]
            )

            comment = self._extract_table_comment(
                [{"col_name": r["col_name"], "data_type": r["data_type"]} for r in desc_rows]
            )

            # Get TBLPROPERTIES
            tblproperties: dict[str, str] = {}
            try:
                props_rows = spark.sql(f"SHOW TBLPROPERTIES {full_table_name}").collect()
                for r in props_rows:
                    tblproperties[r["key"]] = r["value"]
            except Exception:
                pass

            # Get NOT NULL info
            nullable_info = self._get_nullable_info_spark(spark, full_table_name, columns)

            return ExistingTableSchema(
                exists=True,
                columns=nullable_info,
                comment=comment,
                tblproperties=tblproperties,
            )
        except Exception as e:
            logger.warning("Failed to inspect table via Spark: %s", e)
            return ExistingTableSchema(exists=False)

    def _inspect_via_sdk(self, full_table_name: str) -> ExistingTableSchema:
        """Inspect table using Databricks SQL client (Statement Execution API)."""
        assert self._sql_client is not None

        try:
            # DESCRIBE TABLE EXTENDED
            desc_result: QueryResult = self._sql_client.query(f"DESCRIBE TABLE EXTENDED {full_table_name}")
            if not desc_result.success:
                return ExistingTableSchema(exists=False)

            columns = self._parse_describe_rows(desc_result.rows)
            comment = self._extract_table_comment(desc_result.rows)

            # SHOW TBLPROPERTIES
            tblproperties: dict[str, str] = {}
            props_result: QueryResult = self._sql_client.query(f"SHOW TBLPROPERTIES {full_table_name}")
            if props_result.success:
                for row in props_result.rows:
                    key = row.get("key", "")
                    value = row.get("value", "")
                    if key and isinstance(key, str) and isinstance(value, str):
                        tblproperties[key] = value

            # DESCRIBE TABLE EXTENDED gives nullable info in detailed section
            # Re-parse with nullable info from detail
            columns_with_nullable = self._enrich_nullable_info(columns, desc_result.rows)

            return ExistingTableSchema(
                exists=True,
                columns=columns_with_nullable,
                comment=comment,
                tblproperties=tblproperties,
            )
        except Exception as e:
            logger.warning("Failed to inspect table via SDK: %s", e)
            return ExistingTableSchema(exists=False)

    @staticmethod
    def _parse_describe_rows(rows: list[dict[str, Any]]) -> list[ExistingColumn]:
        """Parse DESCRIBE TABLE output into ExistingColumn list.

        DESCRIBE TABLE EXTENDED returns columns first, then a blank separator row,
        then metadata rows starting with '# Detailed Table Information'.
        """
        columns: list[ExistingColumn] = []
        for row in rows:
            col_name = str(row.get("col_name", "")).strip()
            data_type = str(row.get("data_type", "")).strip()

            # Stop at separator or metadata section
            if not col_name or col_name.startswith("#") or not data_type:
                break

            comment_val = row.get("comment", None)
            comment = str(comment_val).strip() if comment_val and str(comment_val).strip() else None

            columns.append(
                ExistingColumn(
                    name=col_name,
                    type=data_type.upper(),
                    nullable=True,  # default; enriched later
                    comment=comment,
                )
            )
        return columns

    @staticmethod
    def _extract_table_comment(rows: list[dict[str, Any]]) -> Optional[str]:
        """Extract table comment from DESCRIBE TABLE EXTENDED output."""
        in_detail = False
        for row in rows:
            col_name = str(row.get("col_name", "")).strip()
            if col_name == "# Detailed Table Information":
                in_detail = True
                continue
            if in_detail and col_name == "Comment":
                data_type = str(row.get("data_type", "")).strip()
                return data_type if data_type else None
        return None

    @staticmethod
    def _enrich_nullable_info(
        columns: list[ExistingColumn],
        desc_rows: list[dict[str, Any]],
    ) -> list[ExistingColumn]:
        """Enrich columns with NOT NULL information from DESCRIBE output.

        In Databricks, DESCRIBE TABLE EXTENDED shows 'NOT NULL' in the data_type
        for columns that have NOT NULL constraints.
        """
        not_null_cols: set[str] = set()

        # Check if data_type contains NOT NULL or if there's a nullable field
        for row in desc_rows:
            col_name = str(row.get("col_name", "")).strip()
            data_type = str(row.get("data_type", "")).strip()
            if not col_name or col_name.startswith("#"):
                break
            if "NOT NULL" in data_type.upper():
                not_null_cols.add(col_name)

        return [
            ExistingColumn(
                name=col.name,
                type=col.type,
                nullable=col.name not in not_null_cols,
                comment=col.comment,
            )
            for col in columns
        ]

    @staticmethod
    def _get_nullable_info_spark(
        spark: Any,
        full_table_name: str,
        columns: list[ExistingColumn],
    ) -> list[ExistingColumn]:
        """Get NOT NULL info from Spark schema."""
        try:
            df = spark.sql(f"SELECT * FROM {full_table_name} LIMIT 0")
            schema_fields = {f.name: f.nullable for f in df.schema.fields}
            return [
                ExistingColumn(
                    name=col.name,
                    type=col.type,
                    nullable=schema_fields.get(col.name, True),
                    comment=col.comment,
                )
                for col in columns
            ]
        except Exception:
            return columns
