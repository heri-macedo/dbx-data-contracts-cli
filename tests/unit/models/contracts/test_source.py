"""
Unit tests for Source model — extra fields validation.

Tests cover:
    - Extra fields rejected on Source (e.g. 'connection_string' not in schema)

Mirrors: databricks_contracts/models/contracts/source.py

Example:
    $ pytest tests/unit/models/contracts/test_source.py -v
"""

import pytest
from pydantic import ValidationError

from databricks_contracts.models.contracts.source import Source


class TestSourceExtraFieldsForbidden:
    """Tests for Source model rejecting unknown/extra fields (extra='forbid')."""

    def test_source_rejects_extra_field(self, sample_source_data: dict) -> None:
        """
        Test that Source rejects an unknown field.

        A user might mistakenly add a 'connection_string' field that does not
        exist in the Source schema. With extra='forbid', this should raise a
        ValidationError.

        Args:
            sample_source_data: Valid source dictionary from fixture.
        """
        # Arrange
        sample_source_data["connection_string"] = "Server=prod;Database=finance;"

        # Act & Assert
        with pytest.raises(ValidationError, match="connection_string"):
            Source.model_validate(sample_source_data)
