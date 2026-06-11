"""Unit tests for PurviewTableEntity.to_json()."""

from databricks_contracts.models.purview.column import PurviewColumnAttributes, PurviewColumnEntity
from databricks_contracts.models.purview.entity import PurviewTableAttributes, PurviewTableEntity


class TestPurviewTableEntityToJson:
    def test_to_json_with_columns(self) -> None:
        attrs = PurviewTableAttributes(
            qualifiedName="databricks://m/cat/sch/tbl",
            name="tbl",
            catalogName="cat",
            schemaName="sch",
        )
        col = PurviewColumnEntity(
            typeName="databricks_table_column",
            attributes=PurviewColumnAttributes(
                qualifiedName="databricks://m/cat/sch/tbl#id",
                name="id",
                dataType="STRING",
                isNullable=False,
                ordinalPosition=0,
            ),
        )
        entity = PurviewTableEntity(attributes=attrs, columns=[col])
        payload = entity.to_json()

        assert "entities" in payload
        # table + 1 column
        assert len(payload["entities"]) == 2
        table_data = payload["entities"][0]
        assert table_data["guid"] == "-1"
        assert "relationshipAttributes" in table_data
        assert len(table_data["relationshipAttributes"]["columns"]) == 1

        col_data = payload["entities"][1]
        assert col_data["guid"] == "-2"
        assert col_data["relationshipAttributes"]["table"]["guid"] == "-1"

    def test_to_json_without_columns(self) -> None:
        attrs = PurviewTableAttributes(
            qualifiedName="databricks://m/cat/sch/tbl",
            name="tbl",
            catalogName="cat",
            schemaName="sch",
        )
        entity = PurviewTableEntity(attributes=attrs, columns=[])
        payload = entity.to_json()

        assert len(payload["entities"]) == 1
        assert "relationshipAttributes" not in payload["entities"][0]

    def test_to_json_multiple_columns(self) -> None:
        attrs = PurviewTableAttributes(
            qualifiedName="databricks://m/cat/sch/tbl",
            name="tbl",
            catalogName="cat",
            schemaName="sch",
        )
        cols = [
            PurviewColumnEntity(
                typeName="databricks_table_column",
                attributes=PurviewColumnAttributes(
                    qualifiedName=f"databricks://m/cat/sch/tbl#col{i}",
                    name=f"col{i}",
                    dataType="STRING",
                    isNullable=True,
                    ordinalPosition=i,
                ),
            )
            for i in range(3)
        ]
        entity = PurviewTableEntity(attributes=attrs, columns=cols)
        payload = entity.to_json()

        # table + 3 columns
        assert len(payload["entities"]) == 4
        # Columns get guids -2, -3, -4
        assert payload["entities"][1]["guid"] == "-2"
        assert payload["entities"][2]["guid"] == "-3"
        assert payload["entities"][3]["guid"] == "-4"
