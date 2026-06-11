"""Query result model for SQL introspection queries."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class QueryResult(BaseModel):
    """Result of a SQL query execution (e.g. DESCRIBE TABLE, SHOW TBLPROPERTIES)."""

    model_config = {"frozen": True}

    success: bool = Field(..., description="Whether the query succeeded")
    rows: list[dict[str, Any]] = Field(default_factory=list, description="Query result rows as dicts")
    error: Optional[str] = Field(default=None, description="Error message if query failed")
