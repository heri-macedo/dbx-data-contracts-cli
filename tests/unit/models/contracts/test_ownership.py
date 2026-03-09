"""
Unit tests for Ownership model — extra fields validation.

Tests cover:
    - Extra fields rejected on Ownership (e.g. 'team_name' not in schema)

Mirrors: databricks_contracts/models/contracts/ownership.py

Example:
    $ pytest tests/unit/models/contracts/test_ownership.py -v
"""

import pytest
from pydantic import ValidationError

from databricks_contracts.models.contracts.ownership import Ownership


class TestOwnershipExtraFieldsForbidden:
    """Tests for Ownership model rejecting unknown/extra fields (extra='forbid')."""

    def test_ownership_rejects_extra_field(self, sample_ownership_data: dict) -> None:
        """
        Test that Ownership rejects an unknown field.

        A user might mistakenly add a 'team_name' field that does not exist
        in the Ownership schema. With extra='forbid', this should raise a
        ValidationError.

        Args:
            sample_ownership_data: Valid ownership dictionary from fixture.
        """
        # Arrange
        sample_ownership_data["team_name"] = "Data Engineering Squad"

        # Act & Assert
        with pytest.raises(ValidationError, match="team_name"):
            Ownership.model_validate(sample_ownership_data)
