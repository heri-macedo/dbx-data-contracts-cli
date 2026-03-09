"""
Tests for databricks-contracts package.

Test structure:
    - unit/: Unit tests for individual modules
        - test_models.py: General contract model tests
        - test_services.py: General service tests
        - models/contracts/: Per-model tests (table, column, contract, ownership, source)
        - services/contracts/: Per-service tests (builder DDL generation)
    - integration/: Integration tests

Test files mirror the source code structure for intuitive navigation:
    databricks_contracts/models/contracts/table.py → tests/unit/models/contracts/test_table.py
    databricks_contracts/services/contracts/builder.py → tests/unit/services/contracts/test_builder.py

Example:
    $ pytest tests/
    $ pytest tests/unit/
    $ pytest tests/unit/models/contracts/test_table.py
"""
