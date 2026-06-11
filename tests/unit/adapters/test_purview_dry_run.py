"""Unit tests for DryRunPurviewClient."""

from databricks_contracts.adapters.purview.dry_run_client import DryRunPurviewClient


class TestDryRunPurviewClient:
    def test_create_or_update_entity(self) -> None:
        client = DryRunPurviewClient()
        payload = {
            "entities": [
                {
                    "typeName": "databricks_table",
                    "attributes": {"qualifiedName": "databricks://m/c/s/t"},
                },
                {
                    "typeName": "databricks_table_column",
                    "attributes": {"qualifiedName": "databricks://m/c/s/t#col"},
                },
            ]
        }
        result = client.create_or_update_entity(payload, "TestCollection", "coll-123")

        assert "guidAssignments" in result
        assert "mutatedEntities" in result
        assert len(result["guidAssignments"]) == 2
        assert "databricks://m/c/s/t" in result["guidAssignments"]
        assert len(result["mutatedEntities"]["CREATE"]) == 2

    def test_get_collection_id_by_friendly_name(self) -> None:
        client = DryRunPurviewClient()
        coll_id, display_name = client.get_collection_id_by_friendly_name("MyCollection")
        assert "dry-run-collection-MyCollection" == coll_id
        assert display_name == "MyCollection"
