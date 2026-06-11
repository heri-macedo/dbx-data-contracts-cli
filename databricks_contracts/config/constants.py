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
    PARTITIONED_BY = "PARTITIONED BY"
    ADD_COLUMNS = "ADD COLUMNS"
    SET_NOT_NULL = "SET NOT NULL"
    DROP_NOT_NULL = "DROP NOT NULL"
    ADD_CONSTRAINT = "ADD CONSTRAINT"
    DROP_CONSTRAINT = "DROP CONSTRAINT"
    CHECK = "CHECK"
    SET_TBLPROPERTIES = "SET TBLPROPERTIES"
    COMMENT_ON_TABLE = "COMMENT ON TABLE"


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
