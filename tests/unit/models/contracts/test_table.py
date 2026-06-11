"""
Unit tests for Table and TableTags models.

Tests cover:
    - partitioned_by with empty list
    - partitioned_by with multiple valid columns
    - partitioned_by with duplicate column names
    - Extra fields rejected on Table (e.g. typo partition_by)
    - Extra fields rejected on TableTags

Mirrors: databricks_contracts/models/contracts/table.py

Example:
    $ pytest tests/unit/models/contracts/test_table.py -v
"""

import pytest
from pydantic import ValidationError

from databricks_contracts.models.contracts.table import Table, TableTags


class TestTablePartitionedBy:
    """Tests for Table.partitioned_by field validation and edge cases."""

    def test_partitioned_by_with_empty_list_raises(self, sample_table_data: dict) -> None:
        """
        Test that partitioned_by with an empty list is rejected.

        An empty list is semantically wrong — use None to omit partitioning.

        Args:
            sample_table_data: Valid table dictionary from fixture.
        """
        # Arrange
        sample_table_data["partitioned_by"] = []

        # Act & Assert
        with pytest.raises(ValidationError, match="empty list"):
            Table.model_validate(sample_table_data)

    def test_partitioned_by_with_multiple_valid_columns(
        self,
        sample_table_data_with_multiple_partitions: dict,
    ) -> None:
        """
        Test that partitioned_by accepts multiple columns that exist in the table.

        The table fixture contains columns order_date and customer_name, so
        partitioning by both should be valid and preserve the column order.

        Args:
            sample_table_data_with_multiple_partitions: Table dict with two partition columns.
        """
        # Arrange
        table_data = sample_table_data_with_multiple_partitions

        # Act
        table = Table.model_validate(table_data)

        # Assert
        assert table.partitioned_by == ["order_date", "customer_name"]
        assert len(table.partitioned_by) == 2

    def test_partitioned_by_with_duplicate_column_names_raises(
        self,
        sample_table_data: dict,
    ) -> None:
        """
        Test that partitioned_by with duplicate column names is rejected.

        Args:
            sample_table_data: Valid table dictionary from fixture.
        """
        # Arrange
        sample_table_data["partitioned_by"] = ["order_date", "order_date"]

        # Act & Assert
        with pytest.raises(ValidationError, match="Duplicate partition column names"):
            Table.model_validate(sample_table_data)


class TestTableExtraFieldsForbidden:
    """Tests for Table model rejecting unknown/extra fields (extra='forbid')."""

    def test_table_rejects_extra_field_partition_by_typo(
        self,
        sample_table_data: dict,
    ) -> None:
        """
        Test that a typo 'partition_by' (instead of 'partitioned_by') is rejected.

        This is the most common typo scenario. With extra='forbid' configured,
        Pydantic should raise a ValidationError indicating that 'partition_by'
        is not a recognized field.

        Args:
            sample_table_data: Valid table dictionary from fixture.
        """
        # Arrange
        sample_table_data["partition_by"] = ["order_date"]

        # Act & Assert
        with pytest.raises(ValidationError, match="partition_by"):
            Table.model_validate(sample_table_data)

    def test_table_rejects_arbitrary_extra_field(
        self,
        sample_table_data: dict,
    ) -> None:
        """
        Test that an arbitrary unknown field is rejected by the Table model.

        Any field not defined in the Table model should cause a ValidationError,
        not just common typos.

        Args:
            sample_table_data: Valid table dictionary from fixture.
        """
        # Arrange
        sample_table_data["unknown_field"] = "some_value"

        # Act & Assert
        with pytest.raises(ValidationError, match="unknown_field"):
            Table.model_validate(sample_table_data)


class TestTableTagsExtraFieldsForbidden:
    """Tests for TableTags model rejecting unknown/extra fields (extra='forbid')."""

    def test_table_tags_rejects_extra_field(self, sample_table_tags_data: dict) -> None:
        """
        Test that TableTags rejects an unknown field.

        For example, a user might mistakenly add a 'tier' tag that does not
        exist in the TableTags schema. With extra='forbid', this should raise
        a ValidationError.

        Args:
            sample_table_tags_data: Valid table tags dictionary from fixture.
        """
        # Arrange
        sample_table_tags_data["tier"] = "premium"

        # Act & Assert
        with pytest.raises(ValidationError, match="tier"):
            TableTags.model_validate(sample_table_tags_data)
