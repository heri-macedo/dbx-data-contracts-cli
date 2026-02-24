"""
Unit tests for models.

Tests for Pydantic models in the models/ module.

Example:
    $ pytest tests/unit/test_models.py -v
"""

import pytest

from databricks_contracts.models import Contract
from databricks_contracts.models.inputs import ApplyInput, ValidateInput
from databricks_contracts.models.statements.tag import TagStatement


class TestContract:
    """Tests for Contract model."""

    def test_contract_parse_valid(self, sample_contract_data: dict) -> None:
        """
        Test that valid contract data parses correctly.

        Args:
            sample_contract_data: Fixture with valid contract data.

        Example:
            >>> contract = Contract.model_validate(data)
            >>> assert contract.name == "test_contract"
        """
        contract = Contract.model_validate(sample_contract_data)

        assert contract.name == "test_contract"
        assert contract.version == "1.0.0"
        assert contract.table.name == "test_table"
        assert len(contract.table.columns) == 2

    def test_contract_full_table_name(self, sample_contract_data: dict) -> None:
        """
        Test full_table_name property.

        Args:
            sample_contract_data: Fixture with valid contract data.

        Example:
            >>> contract.full_table_name
            "test_catalog.test_schema.test_table"
        """
        contract = Contract.model_validate(sample_contract_data)

        assert contract.full_table_name == "test_catalog.test_schema.test_table"

    def test_contract_missing_required_field(self, sample_contract_data: dict) -> None:
        """
        Test that missing required fields raise ValidationError.

        Args:
            sample_contract_data: Fixture with valid contract data.
        """
        from pydantic import ValidationError

        del sample_contract_data["table"]

        with pytest.raises(ValidationError):
            Contract.model_validate(sample_contract_data)


class TestApplyInput:
    """Tests for ApplyInput model."""

    def test_apply_input_valid(self) -> None:
        """
        Test valid ApplyInput creation.

        Example:
            >>> input = ApplyInput(contract_name="test", environment="prod")
            >>> assert input.contract_name == "test"
        """
        input = ApplyInput(contract_name="test_contract", environment="prod")

        assert input.contract_name == "test_contract"
        assert input.environment == "prod"

    def test_apply_input_strips_yaml_extension(self) -> None:
        """
        Test that .yaml extension is stripped from contract_name.

        Example:
            >>> input = ApplyInput(contract_name="test.yaml")
            >>> assert input.contract_name == "test"
        """
        input = ApplyInput(contract_name="test_contract.yaml")

        assert input.contract_name == "test_contract"

    def test_apply_input_default_environment(self) -> None:
        """
        Test default environment is 'dev'.

        Example:
            >>> input = ApplyInput(contract_name="test")
            >>> assert input.environment == "dev"
        """
        input = ApplyInput(contract_name="test")

        assert input.environment == "dev"


class TestValidateInput:
    """Tests for ValidateInput model."""

    def test_validate_input_single(self) -> None:
        """
        Test ValidateInput for single contract.

        Example:
            >>> input = ValidateInput(contract_name="test")
            >>> assert not input.validate_all
        """
        input = ValidateInput(contract_name="test")

        assert input.contract_name == "test"
        assert not input.validate_all

    def test_validate_input_all(self) -> None:
        """
        Test ValidateInput for all contracts.

        Example:
            >>> input = ValidateInput()
            >>> assert input.validate_all
        """
        input = ValidateInput()

        assert input.contract_name is None
        assert input.validate_all


class TestTagStatement:
    def test_statement_escapes_single_quotes_in_tag_values(self) -> None:
        stmt = TagStatement(
            target="table",
            tags={"data_exchange": "source d'eau"},
            full_table_name="`test_catalog`.`test_schema`.`problem_quote_break`",
        )

        sql = stmt.statement
        assert "source d''eau" in sql
        assert "source d'eau" not in sql  # unescaped would break SQL
