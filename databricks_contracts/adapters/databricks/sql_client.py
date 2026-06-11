"""Databricks SQL client for querying table metadata via the Statement Execution API."""

from databricks_contracts.config.logger import get_logger
from databricks_contracts.models.results.query_result import QueryResult

logger = get_logger(__name__)


class DatabricksSQLClient:
    """Executes SQL queries against Databricks via the Statement Execution API.

    Uses the Databricks SDK with WorkspaceClient, which picks up
    DATABRICKS_HOST + credentials from the environment automatically.
    """

    def __init__(self, warehouse_id: str) -> None:
        from databricks.sdk import WorkspaceClient

        self._client = WorkspaceClient()
        self._warehouse_id = warehouse_id

    def query(self, sql: str) -> QueryResult:
        """Execute a SQL query and return rows as list of dicts."""
        try:
            from databricks.sdk.service.sql import StatementState

            result = self._client.statement_execution.execute_statement(
                warehouse_id=self._warehouse_id,
                statement=sql,
                wait_timeout="30s",
            )

            if result.status and result.status.state == StatementState.SUCCEEDED:
                rows = self._parse_result(result)
                return QueryResult(success=True, rows=rows)

            error_msg = ""
            if result.status and result.status.error:
                error_msg = result.status.error.message or "Unknown error"
            return QueryResult(success=False, error=error_msg)

        except Exception as e:
            return QueryResult(success=False, error=str(e))

    @staticmethod
    def _parse_result(result: object) -> list[dict[str, object]]:
        """Parse Statement Execution API result into list of dicts."""
        rows: list[dict[str, object]] = []

        if not hasattr(result, "manifest") or not hasattr(result, "result"):
            return rows

        manifest = result.manifest
        data = result.result

        if not manifest or not data:
            return rows

        columns = [col.name for col in manifest.schema.columns] if manifest.schema and manifest.schema.columns else []

        if data.data_array:
            for row_data in data.data_array:
                row_dict = {}
                for i, col_name in enumerate(columns):
                    row_dict[col_name] = row_data[i] if i < len(row_data) else None
                rows.append(row_dict)

        return rows
