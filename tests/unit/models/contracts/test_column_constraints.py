"""Unit tests for ColumnConstraints model."""

import pytest
from pydantic import ValidationError

from databricks_contracts.models.contracts.column import Column, ColumnConstraints


class TestColumnConstraints:
    """Tests for ColumnConstraints model."""

    def test_check_constraint(self) -> None:
        c = ColumnConstraints(check="age > 0 AND age < 150")
        assert c.check == "age > 0 AND age < 150"

    def test_no_constraints(self) -> None:
        c = ColumnConstraints()
        assert c.check is None

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError, match="unknown"):
            ColumnConstraints(check="age > 0", unknown="bad")  # type: ignore


class TestColumnWithConstraints:
    """Tests for Column with constraints field."""

    def test_column_with_check_constraint(self) -> None:
        col = Column(
            name="age",
            type="INT",
            description="Customer age",
            constraints=ColumnConstraints(check="age > 0"),
        )
        assert col.constraints is not None
        assert col.constraints.check == "age > 0"

    def test_column_without_constraints(self) -> None:
        col = Column(name="id", type="STRING", description="ID")
        assert col.constraints is None

    def test_column_from_dict_with_constraints(self) -> None:
        data = {
            "name": "age",
            "type": "INT",
            "description": "Age",
            "constraints": {"check": "age > 0 AND age < 150"},
        }
        col = Column.model_validate(data)
        assert col.constraints is not None
        assert col.constraints.check == "age > 0 AND age < 150"
