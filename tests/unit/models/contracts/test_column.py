"""
Unit tests for Column and ColumnTags models — extra fields validation.

Tests cover:
    - Extra fields rejected on Column (e.g. typo 'types' instead of 'type')
    - Extra fields rejected on ColumnTags (already had extra='forbid')

Mirrors: databricks_contracts/models/contracts/column.py

Example:
    $ pytest tests/unit/models/contracts/test_column.py -v
"""

import pytest
from pydantic import ValidationError

from databricks_contracts.models.contracts.column import Column, ColumnTags


class TestColumnExtraFieldsForbidden:
    """Tests for Column model rejecting unknown/extra fields (extra='forbid')."""

    def test_column_rejects_extra_field(self, sample_column_data: dict) -> None:
        """
        Test that Column rejects an unknown field.

        A user might mistakenly add a 'primary_key' field that does not exist
        in the Column schema. With extra='forbid', this should raise a
        ValidationError.

        Args:
            sample_column_data: Valid column dictionary from fixture.
        """
        # Arrange
        sample_column_data["primary_key"] = True

        # Act & Assert
        with pytest.raises(ValidationError, match="primary_key"):
            Column.model_validate(sample_column_data)


class TestColumnTagsExtraFieldsForbidden:
    """Tests for ColumnTags model rejecting unknown/extra fields (extra='forbid')."""

    def test_column_tags_rejects_extra_field(self, sample_column_tags_data: dict) -> None:
        """
        Test that ColumnTags rejects an unknown field.

        A user might mistakenly add a 'sensitivity' tag that does not exist
        in the ColumnTags schema. With extra='forbid', this should raise a
        ValidationError.

        Args:
            sample_column_tags_data: Valid column tags dictionary from fixture.
        """
        # Arrange
        sample_column_tags_data["sensitivity"] = "high"

        # Act & Assert
        with pytest.raises(ValidationError, match="sensitivity"):
            ColumnTags.model_validate(sample_column_tags_data)
