"""
Validate handler - Orchestrates contract validation.

Validates contract YAML files against the schema.

Example:
    >>> from databricks_contracts.handlers import ValidateHandler
    >>> from databricks_contracts.models.inputs import ValidateInput
    >>>
    >>> handler = ValidateHandler.create()
    >>> result = handler.handle(ValidateInput(contract_name="orders"))
"""

from pydantic import ValidationError

from databricks_contracts.config.logger import get_logger
from databricks_contracts.models.inputs import ValidateInput
from databricks_contracts.models.results import ValidationResult
from databricks_contracts.services.contracts import ContractLoaderService

logger = get_logger(__name__)


class ValidateHandler:
    """
    Handler for validating contract YAML files.

    Validates contracts against the Pydantic schema.

    Attributes:
        loader: Contract loader service.

    Example:
        >>> # Validate single contract
        >>> handler = ValidateHandler.create()
        >>> result = handler.handle(ValidateInput(contract_name="orders"))
        >>>
        >>> if result.valid:
        ...     print("Contract is valid!")
        ... else:
        ...     print(f"Errors: {result.error}")
        >>>
        >>> # Validate all contracts
        >>> results = handler.handle(ValidateInput())  # No contract_name
    """

    def __init__(self, loader: ContractLoaderService) -> None:
        """
        Initialize the validate handler.

        Args:
            loader: Service for loading contracts.

        Example:
            >>> handler = ValidateHandler(loader)
        """
        self._loader = loader

    @classmethod
    def create(cls) -> "ValidateHandler":
        """
        Create handler with default dependencies.

        Returns:
            Configured ValidateHandler instance.

        Example:
            >>> handler = ValidateHandler.create()
        """
        loader = ContractLoaderService()
        return cls(loader)

    def handle(self, input: ValidateInput) -> ValidationResult | list[ValidationResult]:
        """
        Handle contract validation.

        If contract_name is specified, validates single contract.
        Otherwise, validates all contracts.

        Args:
            input: Input DTO with optional contract name.

        Returns:
            ValidationResult for single contract, or list for all.

        Example:
            >>> # Single contract
            >>> result = handler.handle(ValidateInput(contract_name="orders"))
            >>> print(result.valid)
            >>>
            >>> # All contracts
            >>> results = handler.handle(ValidateInput())
            >>> valid = sum(1 for r in results if r.valid)
        """
        if input.validate_all:
            return self._validate_all()
        else:
            return self._validate_single(input.contract_name)  # type: ignore

    def _validate_single(self, contract_name: str) -> ValidationResult:
        """
        Validate a single contract.

        Args:
            contract_name: Contract name to validate.

        Returns:
            ValidationResult with outcome.
        """
        logger.info("🔍 Validating contract: %s", contract_name)

        try:
            self._loader.load(contract_name)
            logger.info("✅ Valid: %s", contract_name)

            return ValidationResult(
                contract_name=contract_name,
                valid=True,
            )

        except ValidationError as e:
            logger.warning("❌ Invalid: %s (%d errors)", contract_name, e.error_count())

            # Format error messages
            errors = []
            for err in e.errors():
                field = ".".join(str(x) for x in err["loc"])
                msg = err["msg"]
                errors.append(f"{field}: {msg}")

            return ValidationResult(
                contract_name=contract_name,
                valid=False,
                error="; ".join(errors),
                error_count=e.error_count(),
            )

        except Exception as e:
            logger.error("❌ Error: %s - %s", contract_name, str(e))

            return ValidationResult(
                contract_name=contract_name,
                valid=False,
                error=str(e),
                error_count=1,
            )

    def _validate_all(self) -> list[ValidationResult]:
        """
        Validate all contracts.

        Returns:
            List of ValidationResult for each contract.
        """
        contracts = self._loader.list_contracts()

        if not contracts:
            logger.info("No contracts found")
            return []

        logger.info("🔍 Validating %d contracts...", len(contracts))

        results = []
        for contract_name in contracts:
            result = self._validate_single(contract_name)
            results.append(result)

        valid_count = sum(1 for r in results if r.valid)
        invalid_count = len(results) - valid_count

        logger.info("✅ Valid: %d, ❌ Invalid: %d", valid_count, invalid_count)

        return results
