"""
Custom exceptions for the databricks-contracts package.

Provides specific exception types for different error scenarios.

Example:
    >>> from databricks_contracts.exceptions import ContractNotFoundError
    >>> raise ContractNotFoundError("Contract not found: orders.yaml")
"""


class DataContractsError(Exception):
    """
    Base exception for all databricks-contracts errors.

    All custom exceptions should inherit from this class.

    Example:
        >>> try:
        ...     raise DataContractsError("Something went wrong")
        ... except DataContractsError as e:
        ...     print(f"Error: {e}")
    """

    pass


class ContractNotFoundError(DataContractsError):
    """
    Raised when a contract file cannot be found.

    Example:
        >>> raise ContractNotFoundError("Contract not found: orders.yaml")
    """

    pass


class ContractParseError(DataContractsError):
    """
    Raised when a contract file cannot be parsed (invalid YAML).

    Example:
        >>> raise ContractParseError("Invalid YAML in orders.yaml")
    """

    pass


class ContractValidationError(DataContractsError):
    """
    Raised when contract data fails validation.

    Example:
        >>> raise ContractValidationError("Missing required field: table.name")
    """

    pass


class ProjectConfigNotFoundError(DataContractsError):
    """
    Raised when the project configuration file is not found.

    Example:
        >>> raise ProjectConfigNotFoundError("datacontract.config.yaml not found")
    """

    pass


class ExecutionError(DataContractsError):
    """
    Raised when DDL execution fails.

    Example:
        >>> raise ExecutionError("Failed to create table: access denied")
    """

    pass


class SparkSQLError(ExecutionError):
    """Raised when a Spark SQL statement fails.

    Automatically extracts a human-readable message from Py4J / JVM
    exceptions, stripping the Java stack trace and class names.

    Example:
        >>> try:
        ...     spark.sql("ALTER TABLE t SET TAGS ('k'='v')")
        ... except Exception as e:
        ...     raise SparkSQLError(e) from e
    """

    def __init__(self, cause: Exception) -> None:
        self.original = cause
        clean = self._extract_message(str(cause))
        super().__init__(clean)

    @staticmethod
    def _extract_message(raw: str) -> str:
        """Extract a human-readable message from Py4J / JVM exceptions.

        Py4J errors arrive as::

            An error occurred while calling o398.sql.
            : com.databricks...UnauthorizedAccessException: PERMISSION_DENIED: ...
            \\tat com.databricks.managedcatalog...

        This strips the Py4J wrapper, the Java package prefix, and the
        stack trace, keeping the simple class name and message.

        Returns:
            e.g. ``UnauthorizedAccessException: PERMISSION_DENIED: ...``
        """
        for line in raw.splitlines():
            line = line.strip().lstrip(": ")
            if not line or line.startswith("at ") or line.startswith("..."):
                continue
            if line.startswith("An error occurred while calling"):
                continue
            # Strip Java package prefix, keep "SimpleClassName: message"
            # e.g. "com.databricks...UnauthorizedAccessException: MSG" → "UnauthorizedAccessException: MSG"
            if "." in line and ": " in line:
                colon_idx = line.index(": ")
                fqcn = line[:colon_idx]
                simple_name = fqcn.rsplit(".", 1)[-1]
                return f"{simple_name}: {line[colon_idx + 2 :]}"
            return line
        return raw.splitlines()[0] if raw else raw


class TagAssignmentNotAuthorizedError(DataContractsError):
    """Raised when the executing principal lacks permission to assign tag policies.

    This is a non-fatal warning during contract application: the table is
    created successfully but one or more tags could not be applied because
    the Service Principal (or user) is not authorised for the corresponding
    tag policy in Unity Catalog.

    Example:
        >>> raise TagAssignmentNotAuthorizedError(
        ...     "classification",
        ...     "PERMISSION_DENIED: User is not authorized to update the tag "
        ...     "assignment for the following tag policies: classification",
        ... )
    """

    def __init__(self, tag_key: str, detail: str) -> None:
        self.tag_key = tag_key
        super().__init__(f"Not authorised to assign tag '{tag_key}': {detail}")


class TriggerError(DataContractsError):
    """
    Raised when job triggering fails.

    Example:
        >>> raise TriggerError("Failed to trigger job: job not found")
    """

    pass


# ============================================================================
# PURVIEW ERRORS
# ============================================================================


class PurviewError(DataContractsError):
    """
    Base exception for all Purview-related errors.

    All Purview exceptions should inherit from this class.

    Example:
        >>> try:
        ...     client.create_entity(payload)
        ... except PurviewError as e:
        ...     print(f"Purview operation failed: {e}")
    """

    pass


class PurviewAuthenticationError(PurviewError):
    """
    Raised when authentication with Purview fails.

    Example:
        >>> raise PurviewAuthenticationError("Invalid or expired token")
    """

    pass


class PurviewConnectionError(PurviewError):
    """
    Raised when connection to Purview API fails.

    Example:
        >>> raise PurviewConnectionError("Failed to connect to Purview API")
    """

    pass


class PurviewEntityOperationError(PurviewError):
    """
    Raised when entity creation or update fails in Purview.

    Example:
        >>> raise PurviewEntityOperationError("Invalid entity payload: missing qualifiedName")
    """

    pass


class PurviewCollectionNotFoundError(PurviewError):
    """
    Raised when the specified Purview collection does not exist.

    Example:
        >>> raise PurviewCollectionNotFoundError("Collection 'MyCollection' not found")
    """

    pass


class PurviewContractMappingError(PurviewError):
    """
    Raised when mapping a Contract to Purview entity fails.

    This typically wraps Pydantic ValidationError when creating
    Purview models from Contract data.

    Example:
        >>> raise PurviewContractMappingError("Missing required field: ownership.purview_collection")
    """

    pass
