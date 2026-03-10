"""
Unit tests for Contract and ContractInfo models — extra fields validation.

Tests cover:
    - Extra fields rejected on Contract (root level)
    - Extra fields rejected on ContractInfo (contract metadata section)

Mirrors: databricks_contracts/models/contracts/contract.py

Example:
    $ pytest tests/unit/models/contracts/test_contract.py -v
"""

import pytest
from pydantic import ValidationError

from databricks_contracts.models.contracts.contract import Contract, ContractInfo


class TestContractExtraFieldsForbidden:
    """Tests for Contract model rejecting unknown/extra fields (extra='forbid')."""

    def test_contract_rejects_extra_field_at_root(
        self,
        sample_full_contract_data: dict,
    ) -> None:
        """
        Test that Contract rejects an unknown field at the root level.

        A user might mistakenly add a 'description' field at the contract root
        (instead of inside the 'table' section). With extra='forbid', this should
        raise a ValidationError.

        Args:
            sample_full_contract_data: Complete contract dictionary from fixture.
        """
        # Arrange
        sample_full_contract_data["description"] = "This should not be here"

        # Act & Assert
        with pytest.raises(ValidationError, match="description"):
            Contract.model_validate(sample_full_contract_data)

    def test_contract_rejects_extra_field_typo_schema_name(
        self,
        sample_full_contract_data: dict,
    ) -> None:
        """
        Test that Contract rejects a typo 'schema_name' (the correct YAML key is 'schema').

        The Contract model uses alias='schema' for the schema_name field.
        If a user writes 'schema_name' in their YAML, it should be rejected
        as an extra field.

        Args:
            sample_full_contract_data: Complete contract dictionary from fixture.
        """
        # Arrange
        sample_full_contract_data["schema_name"] = "wrong_key"

        # Act & Assert
        with pytest.raises(ValidationError, match="schema_name"):
            Contract.model_validate(sample_full_contract_data)


class TestContractInfoExtraFieldsForbidden:
    """Tests for ContractInfo model rejecting unknown/extra fields (extra='forbid')."""

    def test_contract_info_rejects_extra_field(
        self,
        sample_contract_info_data: dict,
    ) -> None:
        """
        Test that ContractInfo rejects an unknown field.

        A user might mistakenly add an 'author' field in the contract metadata
        section. With extra='forbid', this should raise a ValidationError.

        Args:
            sample_contract_info_data: Valid contract info dictionary from fixture.
        """
        # Arrange
        sample_contract_info_data["author"] = "john.doe@company.com"

        # Act & Assert
        with pytest.raises(ValidationError, match="author"):
            ContractInfo.model_validate(sample_contract_info_data)
