"""Unit tests for TableInspectorService."""

from databricks_contracts.services.databricks.table_inspector import (
    ExistingColumn,
    ExistingTableSchema,
    TableInspectorService,
)


class TestTableInspectorParseDescribe:
    """Tests for parsing DESCRIBE TABLE EXTENDED output."""

    def test_parse_basic_columns(self) -> None:
        rows = [
            {"col_name": "id", "data_type": "string", "comment": "Primary key"},
            {"col_name": "name", "data_type": "string", "comment": "Name"},
            {"col_name": "", "data_type": "", "comment": ""},
            {"col_name": "# Detailed Table Information", "data_type": "", "comment": ""},
        ]
        columns = TableInspectorService._parse_describe_rows(rows)
        assert len(columns) == 2
        assert columns[0].name == "id"
        assert columns[0].type == "STRING"
        assert columns[0].comment == "Primary key"
        assert columns[1].name == "name"

    def test_parse_stops_at_metadata_section(self) -> None:
        rows = [
            {"col_name": "id", "data_type": "string", "comment": None},
            {"col_name": "# Detailed Table Information", "data_type": "", "comment": ""},
            {"col_name": "Database", "data_type": "test_catalog", "comment": ""},
        ]
        columns = TableInspectorService._parse_describe_rows(rows)
        assert len(columns) == 1

    def test_parse_empty_comment_becomes_none(self) -> None:
        rows = [
            {"col_name": "id", "data_type": "string", "comment": ""},
        ]
        columns = TableInspectorService._parse_describe_rows(rows)
        assert columns[0].comment is None


class TestTableInspectorExtractComment:
    """Tests for extracting table comment from DESCRIBE output."""

    def test_extracts_comment_from_detail_section(self) -> None:
        rows = [
            {"col_name": "id", "data_type": "string"},
            {"col_name": "", "data_type": ""},
            {"col_name": "# Detailed Table Information", "data_type": ""},
            {"col_name": "Comment", "data_type": "My table comment"},
        ]
        comment = TableInspectorService._extract_table_comment(rows)
        assert comment == "My table comment"

    def test_returns_none_when_no_comment(self) -> None:
        rows = [
            {"col_name": "id", "data_type": "string"},
            {"col_name": "", "data_type": ""},
            {"col_name": "# Detailed Table Information", "data_type": ""},
            {"col_name": "Database", "data_type": "test_db"},
        ]
        comment = TableInspectorService._extract_table_comment(rows)
        assert comment is None


class TestTableInspectorNullableEnrichment:
    """Tests for NOT NULL enrichment."""

    def test_enrich_with_not_null(self) -> None:
        columns = [
            ExistingColumn(name="id", type="STRING", nullable=True),
            ExistingColumn(name="name", type="STRING", nullable=True),
        ]
        desc_rows = [
            {"col_name": "id", "data_type": "string NOT NULL", "comment": ""},
            {"col_name": "name", "data_type": "string", "comment": ""},
        ]
        enriched = TableInspectorService._enrich_nullable_info(columns, desc_rows)
        assert enriched[0].nullable is False
        assert enriched[1].nullable is True


class TestTableInspectorNoBackend:
    """Tests for when no Spark or SDK is available."""

    def test_returns_not_exists_without_backend(self) -> None:
        inspector = TableInspectorService(sql_client=None, spark_executor=None)
        result = inspector.inspect("`cat`.`sch`.`tbl`")
        assert result == ExistingTableSchema(exists=False)
