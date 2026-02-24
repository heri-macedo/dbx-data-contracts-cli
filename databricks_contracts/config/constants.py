"""
Constants and magic strings.
"""


class DDLKeywords:
    """SQL DDL keywords and patterns."""

    CREATE_TABLE = "CREATE TABLE"
    IF_NOT_EXISTS = "IF NOT EXISTS"
    USING_DELTA = "USING DELTA"
    COMMENT = "COMMENT"
    TBLPROPERTIES = "TBLPROPERTIES"
    ALTER_TABLE = "ALTER TABLE"
    SET_TAGS = "SET TAGS"
    ALTER_COLUMN = "ALTER COLUMN"
    NOT_NULL = "NOT NULL"


class FileNames:
    """Standard file names."""

    PROJECT_CONFIG = "datacontract.config.yaml"


class EnvironmentVariables:
    """Environment variable names."""

    DATABRICKS_RUNTIME_VERSION = "DATABRICKS_RUNTIME_VERSION"
    PROJECT_ROOT = "PROJECT_ROOT"


class Defaults:
    """Default values."""

    RETENTION_DAYS = 90
    REFRESH_FREQUENCY = "daily"
    NULLABLE = True
    TABLE_FORMAT = "DELTA"


class BundleDefaults:
    """Defaults for DAB job generation."""

    SCRIPT_PATH = "resources/scripts/main.py"
    JOB_NAME_PREFIX = "Apply Contract"

    @classmethod
    def job_name(cls, contract_name: str) -> str:
        """Generate job name for a contract."""
        return f"{cls.JOB_NAME_PREFIX} - {contract_name}"
