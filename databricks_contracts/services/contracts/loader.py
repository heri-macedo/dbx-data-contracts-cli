"""
Contract loader service.

Loads and validates contract YAML files.

Example:
    >>> from databricks_contracts.services.contracts import ContractLoaderService
    >>> loader = ContractLoaderService()
    >>> contract = loader.load("orders_v1")
    >>> print(contract.table.name)
"""

from pathlib import Path
from typing import Any

import yaml

from databricks_contracts.exceptions import ContractNotFoundError, ContractParseError
from databricks_contracts.models.contracts import Contract
from databricks_contracts.services.paths import PathResolverService


class ContractLoaderService:
    """
    Service for loading and validating contract YAML files.

    Provides methods to load individual contracts or list all available contracts.

    Attributes:
        contracts_path: Resolved path to contracts directory.

    Example:
        >>> # Create with auto-resolved path
        >>> loader = ContractLoaderService()
        >>>
        >>> # Create with explicit path
        >>> loader = ContractLoaderService(Path("/path/to/contracts"))
        >>>
        >>> # Load a contract
        >>> contract = loader.load("orders_v1")
        >>> print(contract.name)
        "orders_v1"
        >>>
        >>> # List all contracts
        >>> contracts = loader.list_contracts()
        >>> print(contracts)
        ["orders_v1", "customers_v1", "transactions"]
    """

    def __init__(self, contracts_path: Path | None = None) -> None:
        """
        Initialize the loader service.

        Args:
            contracts_path: Path to contracts directory. If None, auto-resolves.

        Example:
            >>> loader = ContractLoaderService()  # Auto-resolve
            >>> loader = ContractLoaderService(Path("./contracts"))  # Explicit
        """
        if contracts_path is None:
            contracts_path = PathResolverService.create().contracts_path
        self._contracts_path = contracts_path

    @property
    def contracts_path(self) -> Path:
        """
        Get the contracts directory path.

        Returns:
            Path to contracts directory.

        Example:
            >>> loader.contracts_path
            Path("/project/contracts")
        """
        return self._contracts_path

    def get_contract_path(self, contract_name: str) -> Path:
        """
        Get the full path to a contract file.

        Args:
            contract_name: Contract name without .yaml extension.

        Returns:
            Full path to the contract file.

        Example:
            >>> loader.get_contract_path("orders")
            Path("/project/contracts/orders.yaml")
        """
        return self._contracts_path / f"{contract_name}.yaml"

    def load_raw(self, contract_name: str) -> dict[str, Any]:
        """
        Load a contract from disk as raw dictionary (without validation).

        Args:
            contract_name: Contract name without .yaml extension.

        Returns:
            Raw dictionary from YAML file.

        Raises:
            ContractNotFoundError: If file doesn't exist.
            ContractParseError: If YAML is invalid.

        Example:
            >>> data = loader.load_raw("orders")
            >>> print(data["table"]["name"])
        """
        path = self.get_contract_path(contract_name)

        if not path.exists():
            raise ContractNotFoundError(f"Contract not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                contract_data: dict[str, Any] = yaml.safe_load(f)
                return contract_data
        except yaml.YAMLError as e:
            raise ContractParseError(f"Failed to parse {contract_name}: {e}") from e

    def load(self, contract_name: str) -> Contract:
        """
        Load and validate a contract, returning Contract model.

        Args:
            contract_name: Contract name without .yaml extension.

        Returns:
            Validated Contract model.

        Raises:
            ContractNotFoundError: If file doesn't exist.
            ContractParseError: If YAML is invalid.
            ValidationError: If contract data fails validation.

        Example:
            >>> contract = loader.load("orders_v1")
            >>> print(contract.name)
            "orders_v1"
            >>> print(contract.table.columns[0].name)
            "order_id"
        """
        contract_data = self.load_raw(contract_name)
        return Contract.model_validate(contract_data)

    def list_contracts(self) -> list[str]:
        """
        List all available contract names.

        Returns:
            Sorted list of contract names (without extension).

        Example:
            >>> loader.list_contracts()
            ["customers_v1", "orders_v1", "transactions_daily"]
        """
        if not self._contracts_path.exists():
            return []
        return sorted([p.stem for p in self._contracts_path.glob("*.yaml") if p.is_file()])

    def exists(self, contract_name: str) -> bool:
        """
        Check if a contract file exists.

        Args:
            contract_name: Contract name without .yaml extension.

        Returns:
            True if contract file exists.

        Example:
            >>> loader.exists("orders_v1")
            True
            >>> loader.exists("nonexistent")
            False
        """
        return self.get_contract_path(contract_name).exists()
