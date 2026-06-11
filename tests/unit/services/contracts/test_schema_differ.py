"""Unit tests for SchemaDifferService.

These tests verify that mutations to the diff logic are caught:
- Each DiffType enum value is asserted exactly (not just filtered).
- is_safe flags are explicitly checked per scenario.
- current_value / desired_value are asserted precisely.
- The _SAFE_TYPE_WIDENINGS table is exercised per entry.
"""

import pytest

from databricks_contracts.models.contracts.contract import Contract
from databricks_contracts.services.contracts.schema_differ import (
    DiffType,
    SchemaDiff,
    SchemaDifferService,
)
from databricks_contracts.services.databricks.table_inspector import (
    ExistingColumn,
    ExistingTableSchema,
)

# -- Helpers ------------------------------------------------------------------

MATCHING_TBLPROPERTIES = {
    "refresh_frequency": "daily",
    "retention_days": "90",
    "delta.deletedFileRetentionDuration": "interval 90 days",
    "delta.logRetentionDuration": "interval 90 days",
}


def _existing(
    columns: list[ExistingColumn] | None = None,
    comment: str = "Test table",
    tblproperties: dict[str, str] | None = None,
) -> ExistingTableSchema:
    """Build an ExistingTableSchema with sensible defaults."""
    return ExistingTableSchema(
        exists=True,
        columns=columns
        or [
            ExistingColumn(name="id", type="STRING", nullable=False, comment="Primary key"),
            ExistingColumn(name="name", type="STRING", nullable=True, comment="Name"),
        ],
        comment=comment,
        tblproperties=tblproperties or MATCHING_TBLPROPERTIES,
    )


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def base_contract_data() -> dict:
    """Base contract data matching the default _existing() schema."""
    return {
        "contract": {"name": "test_v1", "version": "1.0.0", "status": "active"},
        "catalog": "test_catalog",
        "schema": "test_schema",
        "ownership": {
            "data_owner": "test@example.com",
            "bds": "bds@example.com",
            "tds": "tds@example.com",
            "purview_collection": "TestCollection",
            "portfolio": "Portfolio_1",
            "sub_domain": "Sub_Domain_1",
            "business_description": "Test",
        },
        "table": {
            "name": "test_table",
            "description": "Test table",
            "refresh_frequency": "daily",
            "retention_days": 90,
            "tags": {"layer": "Gold"},
            "columns": [
                {"name": "id", "type": "STRING", "description": "Primary key", "nullable": False},
                {"name": "name", "type": "STRING", "description": "Name", "nullable": True},
            ],
        },
    }


@pytest.fixture
def differ() -> SchemaDifferService:
    return SchemaDifferService()


# -- Tests: no diffs -----------------------------------------------------------


class TestSchemaDifferNoDiffs:
    def test_identical_schema_returns_empty_list(self, base_contract_data: dict, differ: SchemaDifferService) -> None:
        contract = Contract.model_validate(base_contract_data)
        diffs = differ.diff(contract, _existing())
        assert diffs == []

    def test_nonexistent_table_returns_empty_list(self, base_contract_data: dict, differ: SchemaDifferService) -> None:
        contract = Contract.model_validate(base_contract_data)
        diffs = differ.diff(contract, ExistingTableSchema(exists=False))
        assert diffs == []


# -- Tests: column-level diffs ------------------------------------------------


class TestSchemaDifferAddColumn:
    def test_new_column_produces_add_diff(self, base_contract_data: dict, differ: SchemaDifferService) -> None:
        base_contract_data["table"]["columns"].append(
            {"name": "email", "type": "STRING", "description": "Email", "nullable": True}
        )
        contract = Contract.model_validate(base_contract_data)
        diffs = differ.diff(contract, _existing())

        add_diffs = [d for d in diffs if d.diff_type == DiffType.ADD_COLUMN]
        assert len(add_diffs) == 1

        d = add_diffs[0]
        assert d.diff_type == DiffType.ADD_COLUMN
        assert d.column_name == "email"
        assert d.desired_value == "STRING"
        assert d.is_safe is True


class TestSchemaDifferRemoveColumn:
    def test_extra_existing_column_produces_remove_diff(
        self, base_contract_data: dict, differ: SchemaDifferService
    ) -> None:
        existing = _existing(
            columns=[
                ExistingColumn(name="id", type="STRING", nullable=False, comment="Primary key"),
                ExistingColumn(name="name", type="STRING", nullable=True, comment="Name"),
                ExistingColumn(name="old_col", type="INT", nullable=True),
            ],
        )
        contract = Contract.model_validate(base_contract_data)
        diffs = differ.diff(contract, existing)

        remove_diffs = [d for d in diffs if d.diff_type == DiffType.REMOVE_COLUMN]
        assert len(remove_diffs) == 1

        d = remove_diffs[0]
        assert d.diff_type == DiffType.REMOVE_COLUMN
        assert d.column_name == "old_col"
        assert d.current_value == "INT"
        assert d.is_safe is False


class TestSchemaDifferModifyColumnComment:
    def test_changed_comment_produces_diff(self, base_contract_data: dict, differ: SchemaDifferService) -> None:
        existing = _existing(
            columns=[
                ExistingColumn(name="id", type="STRING", nullable=False, comment="Old comment"),
                ExistingColumn(name="name", type="STRING", nullable=True, comment="Name"),
            ],
        )
        contract = Contract.model_validate(base_contract_data)
        diffs = differ.diff(contract, existing)

        comment_diffs = [d for d in diffs if d.diff_type == DiffType.MODIFY_COLUMN_COMMENT]
        assert len(comment_diffs) == 1

        d = comment_diffs[0]
        assert d.diff_type == DiffType.MODIFY_COLUMN_COMMENT
        assert d.column_name == "id"
        assert d.current_value == "Old comment"
        assert d.desired_value == "Primary key"
        assert d.is_safe is True

    def test_none_comment_treated_as_empty_string(self, base_contract_data: dict, differ: SchemaDifferService) -> None:
        """Existing column with comment=None should compare as ''."""
        existing = _existing(
            columns=[
                ExistingColumn(name="id", type="STRING", nullable=False, comment=None),
                ExistingColumn(name="name", type="STRING", nullable=True, comment="Name"),
            ],
        )
        contract = Contract.model_validate(base_contract_data)
        diffs = differ.diff(contract, existing)

        comment_diffs = [d for d in diffs if d.diff_type == DiffType.MODIFY_COLUMN_COMMENT]
        assert len(comment_diffs) == 1
        assert comment_diffs[0].current_value == ""
        assert comment_diffs[0].desired_value == "Primary key"


class TestSchemaDifferModifyNullability:
    def test_nullable_to_not_null(self, base_contract_data: dict, differ: SchemaDifferService) -> None:
        existing = _existing(
            columns=[
                ExistingColumn(name="id", type="STRING", nullable=True, comment="Primary key"),
                ExistingColumn(name="name", type="STRING", nullable=True, comment="Name"),
            ],
        )
        contract = Contract.model_validate(base_contract_data)
        diffs = differ.diff(contract, existing)

        null_diffs = [d for d in diffs if d.diff_type == DiffType.MODIFY_COLUMN_NULLABILITY]
        assert len(null_diffs) == 1

        d = null_diffs[0]
        assert d.diff_type == DiffType.MODIFY_COLUMN_NULLABILITY
        assert d.column_name == "id"
        assert d.current_value == "nullable"
        assert d.desired_value == "NOT NULL"

    def test_not_null_to_nullable(self, base_contract_data: dict, differ: SchemaDifferService) -> None:
        base_contract_data["table"]["columns"][1]["nullable"] = True
        existing = _existing(
            columns=[
                ExistingColumn(name="id", type="STRING", nullable=False, comment="Primary key"),
                ExistingColumn(name="name", type="STRING", nullable=False, comment="Name"),
            ],
        )
        contract = Contract.model_validate(base_contract_data)
        diffs = differ.diff(contract, existing)

        null_diffs = [d for d in diffs if d.diff_type == DiffType.MODIFY_COLUMN_NULLABILITY]
        assert len(null_diffs) == 1
        assert null_diffs[0].current_value == "NOT NULL"
        assert null_diffs[0].desired_value == "nullable"


class TestSchemaDifferModifyType:
    def test_safe_type_widening_int_to_bigint(self, base_contract_data: dict, differ: SchemaDifferService) -> None:
        base_contract_data["table"]["columns"][0] = {
            "name": "id",
            "type": "BIGINT",
            "description": "Primary key",
            "nullable": False,
        }
        existing = _existing(
            columns=[
                ExistingColumn(name="id", type="INT", nullable=False, comment="Primary key"),
                ExistingColumn(name="name", type="STRING", nullable=True, comment="Name"),
            ],
        )
        contract = Contract.model_validate(base_contract_data)
        diffs = differ.diff(contract, existing)

        type_diffs = [d for d in diffs if d.diff_type == DiffType.MODIFY_COLUMN_TYPE]
        assert len(type_diffs) == 1

        d = type_diffs[0]
        assert d.diff_type == DiffType.MODIFY_COLUMN_TYPE
        assert d.column_name == "id"
        assert d.current_value == "INT"
        assert d.desired_value == "BIGINT"
        assert d.is_safe is True

    def test_unsafe_type_narrowing_bigint_to_int(self, base_contract_data: dict, differ: SchemaDifferService) -> None:
        base_contract_data["table"]["columns"][0] = {
            "name": "id",
            "type": "INT",
            "description": "Primary key",
            "nullable": False,
        }
        existing = _existing(
            columns=[
                ExistingColumn(name="id", type="BIGINT", nullable=False, comment="Primary key"),
                ExistingColumn(name="name", type="STRING", nullable=True, comment="Name"),
            ],
        )
        contract = Contract.model_validate(base_contract_data)
        diffs = differ.diff(contract, existing)

        type_diffs = [d for d in diffs if d.diff_type == DiffType.MODIFY_COLUMN_TYPE]
        assert len(type_diffs) == 1
        assert type_diffs[0].is_safe is False
        assert type_diffs[0].current_value == "BIGINT"
        assert type_diffs[0].desired_value == "INT"


# -- Tests: table-level diffs -------------------------------------------------


class TestSchemaDifferTableComment:
    def test_table_comment_change(self, base_contract_data: dict, differ: SchemaDifferService) -> None:
        existing = _existing(comment="Old description")
        contract = Contract.model_validate(base_contract_data)
        diffs = differ.diff(contract, existing)

        comment_diffs = [d for d in diffs if d.diff_type == DiffType.UPDATE_TABLE_COMMENT]
        assert len(comment_diffs) == 1

        d = comment_diffs[0]
        assert d.diff_type == DiffType.UPDATE_TABLE_COMMENT
        assert d.current_value == "Old description"
        assert d.desired_value == "Test table"

    def test_none_table_comment_treated_as_empty(self, base_contract_data: dict, differ: SchemaDifferService) -> None:
        existing = _existing(comment=None)
        contract = Contract.model_validate(base_contract_data)
        diffs = differ.diff(contract, existing)

        comment_diffs = [d for d in diffs if d.diff_type == DiffType.UPDATE_TABLE_COMMENT]
        assert len(comment_diffs) == 1
        assert comment_diffs[0].current_value == ""


class TestSchemaDifferTblproperties:
    def test_tblproperties_change(self, base_contract_data: dict, differ: SchemaDifferService) -> None:
        existing = _existing(tblproperties={"refresh_frequency": "hourly", "retention_days": "30"})
        contract = Contract.model_validate(base_contract_data)
        diffs = differ.diff(contract, existing)

        prop_diffs = [d for d in diffs if d.diff_type == DiffType.UPDATE_TBLPROPERTIES]
        assert len(prop_diffs) == 1
        assert prop_diffs[0].diff_type == DiffType.UPDATE_TBLPROPERTIES
        assert "daily" in prop_diffs[0].desired_value
        assert "90" in prop_diffs[0].desired_value

    def test_no_tblproperties_diff_when_all_match(self, base_contract_data: dict, differ: SchemaDifferService) -> None:
        existing = _existing(tblproperties=MATCHING_TBLPROPERTIES)
        contract = Contract.model_validate(base_contract_data)
        diffs = differ.diff(contract, existing)

        prop_diffs = [d for d in diffs if d.diff_type == DiffType.UPDATE_TBLPROPERTIES]
        assert prop_diffs == []


# -- Tests: _is_safe_type_widening lookup table --------------------------------


class TestSafeTypeWidening:
    """Directly test the type widening table to catch mutations to individual entries."""

    @pytest.mark.parametrize(
        "current_type,desired_type",
        [
            ("TINYINT", "SMALLINT"),
            ("TINYINT", "INT"),
            ("TINYINT", "BIGINT"),
            ("TINYINT", "FLOAT"),
            ("TINYINT", "DOUBLE"),
            ("TINYINT", "DECIMAL"),
            ("SMALLINT", "INT"),
            ("SMALLINT", "BIGINT"),
            ("SMALLINT", "FLOAT"),
            ("SMALLINT", "DOUBLE"),
            ("SMALLINT", "DECIMAL"),
            ("INT", "BIGINT"),
            ("INT", "FLOAT"),
            ("INT", "DOUBLE"),
            ("INT", "DECIMAL"),
            ("BIGINT", "FLOAT"),
            ("BIGINT", "DOUBLE"),
            ("BIGINT", "DECIMAL"),
            ("FLOAT", "DOUBLE"),
            ("BYTE", "SHORT"),
            ("BYTE", "INT"),
            ("BYTE", "BIGINT"),
            ("SHORT", "INT"),
            ("SHORT", "BIGINT"),
        ],
    )
    def test_safe_widening_returns_true(self, current_type: str, desired_type: str) -> None:
        assert SchemaDifferService._is_safe_type_widening(current_type, desired_type) is True

    @pytest.mark.parametrize(
        "current_type,desired_type",
        [
            ("BIGINT", "INT"),
            ("DOUBLE", "FLOAT"),
            ("STRING", "INT"),
            ("INT", "STRING"),
            ("DECIMAL", "INT"),
            ("FLOAT", "INT"),
        ],
    )
    def test_unsafe_narrowing_returns_false(self, current_type: str, desired_type: str) -> None:
        assert SchemaDifferService._is_safe_type_widening(current_type, desired_type) is False

    def test_unknown_type_returns_false(self) -> None:
        assert SchemaDifferService._is_safe_type_widening("BLOB", "STRING") is False


# -- Tests: DiffType enum values -----------------------------------------------


class TestDiffTypeEnumValues:
    """Assert exact enum values to catch mutations like 'add_column' -> 'XXadd_columnXX'."""

    def test_add_column_value(self) -> None:
        assert DiffType.ADD_COLUMN.value == "add_column"

    def test_modify_column_comment_value(self) -> None:
        assert DiffType.MODIFY_COLUMN_COMMENT.value == "modify_column_comment"

    def test_modify_column_nullability_value(self) -> None:
        assert DiffType.MODIFY_COLUMN_NULLABILITY.value == "modify_column_nullability"

    def test_modify_column_type_value(self) -> None:
        assert DiffType.MODIFY_COLUMN_TYPE.value == "modify_column_type"

    def test_remove_column_value(self) -> None:
        assert DiffType.REMOVE_COLUMN.value == "remove_column"

    def test_update_table_comment_value(self) -> None:
        assert DiffType.UPDATE_TABLE_COMMENT.value == "update_table_comment"

    def test_update_tblproperties_value(self) -> None:
        assert DiffType.UPDATE_TBLPROPERTIES.value == "update_tblproperties"


# -- Tests: SchemaDiff defaults ------------------------------------------------


class TestSchemaDiffDefaults:
    def test_is_safe_defaults_to_true(self) -> None:
        d = SchemaDiff(diff_type=DiffType.ADD_COLUMN, column_name="x")
        assert d.is_safe is True

    def test_optional_fields_default_to_none(self) -> None:
        d = SchemaDiff(diff_type=DiffType.ADD_COLUMN)
        assert d.column_name is None
        assert d.current_value is None
        assert d.desired_value is None
