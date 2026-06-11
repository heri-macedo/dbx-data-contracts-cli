"""Schema diff service for comparing contract definitions against existing tables."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from databricks_contracts.models.contracts.contract import Contract
from databricks_contracts.services.databricks.table_inspector import ExistingTableSchema


class DiffType(str, Enum):
    """Types of schema differences between contract and existing table."""

    ADD_COLUMN = "add_column"
    MODIFY_COLUMN_COMMENT = "modify_column_comment"
    MODIFY_COLUMN_NULLABILITY = "modify_column_nullability"
    MODIFY_COLUMN_TYPE = "modify_column_type"
    REMOVE_COLUMN = "remove_column"
    UPDATE_TABLE_COMMENT = "update_table_comment"
    UPDATE_TBLPROPERTIES = "update_tblproperties"


class SchemaDiff(BaseModel):
    """Represents a single difference between contract and existing table."""

    model_config = {"frozen": True}

    diff_type: DiffType
    column_name: Optional[str] = None
    current_value: Optional[str] = None
    desired_value: Optional[str] = None
    is_safe: bool = Field(default=True, description="Whether this change can be auto-applied safely")


# Type widenings that Delta Lake supports safely
_SAFE_TYPE_WIDENINGS: dict[str, set[str]] = {
    "TINYINT": {"SMALLINT", "INT", "BIGINT", "FLOAT", "DOUBLE", "DECIMAL"},
    "SMALLINT": {"INT", "BIGINT", "FLOAT", "DOUBLE", "DECIMAL"},
    "INT": {"BIGINT", "FLOAT", "DOUBLE", "DECIMAL"},
    "BIGINT": {"FLOAT", "DOUBLE", "DECIMAL"},
    "FLOAT": {"DOUBLE"},
    "BYTE": {"SHORT", "INT", "BIGINT"},
    "SHORT": {"INT", "BIGINT"},
}


class SchemaDifferService:
    """Computes differences between a contract definition and an existing table."""

    def diff(self, contract: Contract, existing: ExistingTableSchema) -> list[SchemaDiff]:
        """Compute all diffs between contract and existing table.

        Args:
            contract: The desired contract state.
            existing: The current table state in Unity Catalog.

        Returns:
            List of SchemaDiff describing each difference.
        """
        if not existing.exists:
            return []

        diffs: list[SchemaDiff] = []

        existing_cols = {col.name.lower(): col for col in existing.columns}
        contract_cols = {col.name.lower(): col for col in contract.table.columns}

        # Column-level diffs
        for col in contract.table.columns:
            col_key = col.name.lower()
            if col_key not in existing_cols:
                # New column
                diffs.append(
                    SchemaDiff(
                        diff_type=DiffType.ADD_COLUMN,
                        column_name=col.name,
                        desired_value=col.type.upper(),
                    )
                )
            else:
                existing_col = existing_cols[col_key]

                # Type change
                if col.type.upper() != existing_col.type.upper():
                    is_safe = self._is_safe_type_widening(existing_col.type.upper(), col.type.upper())
                    diffs.append(
                        SchemaDiff(
                            diff_type=DiffType.MODIFY_COLUMN_TYPE,
                            column_name=col.name,
                            current_value=existing_col.type,
                            desired_value=col.type.upper(),
                            is_safe=is_safe,
                        )
                    )

                # Comment change
                current_comment = existing_col.comment or ""
                desired_comment = col.description
                if current_comment != desired_comment:
                    diffs.append(
                        SchemaDiff(
                            diff_type=DiffType.MODIFY_COLUMN_COMMENT,
                            column_name=col.name,
                            current_value=current_comment,
                            desired_value=desired_comment,
                        )
                    )

                # Nullability change
                if col.nullable != existing_col.nullable:
                    diffs.append(
                        SchemaDiff(
                            diff_type=DiffType.MODIFY_COLUMN_NULLABILITY,
                            column_name=col.name,
                            current_value="nullable" if existing_col.nullable else "NOT NULL",
                            desired_value="nullable" if col.nullable else "NOT NULL",
                        )
                    )

        # Columns in table but not in contract (removed)
        for col_key, existing_col in existing_cols.items():
            if col_key not in contract_cols:
                diffs.append(
                    SchemaDiff(
                        diff_type=DiffType.REMOVE_COLUMN,
                        column_name=existing_col.name,
                        current_value=existing_col.type,
                        is_safe=False,
                    )
                )

        # Table comment change
        existing_comment = existing.comment or ""
        desired_comment = contract.table.description
        if existing_comment != desired_comment:
            diffs.append(
                SchemaDiff(
                    diff_type=DiffType.UPDATE_TABLE_COMMENT,
                    current_value=existing_comment,
                    desired_value=desired_comment,
                )
            )

        # TBLPROPERTIES change
        desired_props = {
            "refresh_frequency": contract.table.refresh_frequency.value,
            "retention_days": str(contract.table.retention_days),
            "delta.deletedFileRetentionDuration": f"interval {contract.table.retention_days} days",
            "delta.logRetentionDuration": f"interval {contract.table.retention_days} days",
        }

        props_changed = False
        for key, desired_val in desired_props.items():
            if existing.tblproperties.get(key) != desired_val:
                props_changed = True
                break

        if props_changed:
            diffs.append(
                SchemaDiff(
                    diff_type=DiffType.UPDATE_TBLPROPERTIES,
                    current_value=str(existing.tblproperties),
                    desired_value=str(desired_props),
                )
            )

        return diffs

    @staticmethod
    def _is_safe_type_widening(current_type: str, desired_type: str) -> bool:
        """Check if a type change is a safe widening operation."""
        allowed = _SAFE_TYPE_WIDENINGS.get(current_type, set())
        return desired_type in allowed
