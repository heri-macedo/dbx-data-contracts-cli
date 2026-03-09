# databricks_contracts

Python library for deploying data contracts to Databricks Unity Catalog and publishing metadata to Microsoft Purview.

## Architecture

Clean Architecture with layered separation:

```
databricks_contracts/
├── commands/                   # CLI Layer (Typer)
│   ├── main.py                 # Entry point & router
│   ├── apply.py                # apply contract <name>
│   ├── validate.py             # validate contract/all
│   ├── trigger.py              # trigger contracts/modified/all
│   ├── publish.py              # publish purview/purview-modified/purview-all
│   └── shared/
│       └── output.py           # Rich output formatters
│
├── handlers/                   # Orchestration Layer
│   ├── apply_handler.py        # ApplyHandler.handle(ApplyInput) -> RunResult
│   ├── validate_handler.py     # ValidateHandler.handle(ValidateInput) -> ValidationResult
│   ├── trigger_handler.py      # TriggerHandler.handle(TriggerInput) -> list[TriggerResult]
│   └── publish_handler.py      # PublishHandler.handle(PublishInput) -> PublishResult
│
├── services/                   # Business Logic Layer
│   ├── contracts/
│   │   ├── loader.py           # ContractLoaderService (YAML → Contract)
│   │   └── builder.py          # BuilderService (Contract → DDL statements)
│   ├── git/
│   │   └── change_detector.py  # ChangeDetectorService (git diff)
│   ├── databricks/
│   │   └── trigger.py          # TriggerService (job triggering)
│   ├── purview/
│   │   ├── purview_publisher.py      # PurviewPublisherService
│   │   └── contract_to_purview_mapper.py  # ContractToPurviewMapper
│   └── paths/
│       ├── path_resolver.py    # PathResolverService
│       └── strategies/         # LocalPathStrategy, DatabricksPathStrategy
│
├── adapters/                   # External Integrations
│   ├── databricks/
│   │   ├── api_client.py       # DatabricksClient (Jobs API)
│   │   ├── job_generator.py    # ContractJobGenerator (DAB)
│   │   └── executors/
│   │       ├── base.py         # BaseExecutor (interface)
│   │       ├── spark.py        # SparkExecutor (production)
│   │       └── dry_run.py      # DryRunExecutor (preview)
│   ├── git/
│   │   ├── base.py             # ChangeDetectorPort (interface)
│   │   └── subprocess_adapter.py  # SubprocessGitAdapter
│   └── purview/
│       ├── base.py             # BasePurviewClient (interface)
│       ├── api_client.py       # PurviewCatalogApiClient (Azure SDK)
│       └── dry_run_client.py   # DryRunPurviewClient (preview)
│
├── models/                     # Pydantic Models (extra="forbid" on all contract models)
│   ├── contracts/              # Domain models
│   │   ├── contract.py         # Contract, ContractInfo
│   │   ├── table.py            # Table, TableTags (supports partitioned_by)
│   │   ├── column.py           # Column, ColumnTags
│   │   ├── ownership.py        # Ownership
│   │   ├── source.py           # Source
│   │   └── enums.py            # Layer, Portfolio, etc.
│   ├── inputs/                 # Handler input DTOs
│   │   ├── apply_input.py      # ApplyInput
│   │   ├── validate_input.py   # ValidateInput
│   │   ├── trigger_input.py    # TriggerInput
│   │   └── publish_input.py    # PublishInput
│   ├── results/                # Handler output DTOs
│   │   ├── run_result.py       # RunResult
│   │   ├── validation_result.py # ValidationResult
│   │   ├── trigger_result.py   # TriggerResult
│   │   ├── execution_result.py # ExecutionResult
│   │   └── publish_result.py   # PublishResult
│   ├── statements/             # DDL statement models
│   │   ├── base.py             # BaseStatement (abstract)
│   │   ├── create_table.py     # CreateTableStatement
│   │   └── tag.py              # TagStatement
│   └── purview/                # Purview entity models
│       ├── entity.py           # PurviewTableEntity, PurviewTableAttributes
│       ├── column.py           # PurviewColumnEntity, PurviewColumnAttributes
│       ├── contact.py          # PurviewContact, PurviewContactList
│       └── classification.py   # PurviewClassification
│
├── config/                     # Configuration
│   ├── settings.py             # Settings (env vars via Pydantic)
│   ├── project_config_model.py # ProjectConfig (datacontract.config.yaml)
│   ├── constants.py            # Constants
│   └── logger.py               # Logger utility
│
└── exceptions.py               # Custom exceptions
```

## Design Patterns

### Dependency Injection with Factory Methods

Handlers use factory methods for production and constructor injection for testing:

```python
class ApplyHandler:
    def __init__(
        self,
        loader: ContractLoaderService,
        builder: BuilderService,
        executor: BaseExecutor,
    ):
        self._loader = loader
        self._builder = builder
        self._executor = executor

    @classmethod
    def create(cls, environment: str = "dev", dry_run: bool = False):
        """Factory for production use."""
        loader = ContractLoaderService()
        builder = BuilderService(environment=environment)
        executor = DryRunExecutor() if dry_run else SparkExecutor()
        return cls(loader, builder, executor)

# Production
handler = ApplyHandler.create(environment="prod")

# Testing (inject mocks)
handler = ApplyHandler(mock_loader, mock_builder, mock_executor)
```

### Strategy Pattern (Executors)

```python
class BaseExecutor(ABC):
    @abstractmethod
    def execute(self, statement: BaseStatement) -> ExecutionResult:
        pass

class SparkExecutor(BaseExecutor):
    def execute(self, statement):
        self.spark.sql(statement.statement)
        return ExecutionResult(statement=statement.statement, success=True)

class DryRunExecutor(BaseExecutor):
    def execute(self, statement):
        logger.info(f"[DRY RUN] {statement.log_message}")
        return ExecutionResult(statement=statement.statement, success=True, dry_run=True)
```

### Adapter Pattern (Git)

```python
class ChangeDetectorPort(ABC):
    @abstractmethod
    def get_modified_files(self, base_ref: str, head_ref: str) -> list[str]:
        pass

class SubprocessGitAdapter(ChangeDetectorPort):
    def get_modified_files(self, base_ref, head_ref):
        result = subprocess.run(["git", "diff", "--name-only", base_ref, head_ref], ...)
        return result.stdout.strip().split("\n")

# MockGitAdapter is available in tests/mocks/ for testing
```

## Layer Responsibilities

### Commands (CLI Layer)

- Parse CLI arguments
- Create handlers via factory methods
- Build input DTOs
- Call `handler.handle(input)`
- Format and display output
- Set exit codes

### Handlers (Orchestration Layer)

- Receive input DTOs
- Coordinate service calls
- Handle errors and logging
- Return result DTOs

### Services (Business Logic Layer)

- Pure business logic
- No I/O directly (use adapters)
- Stateless operations

### Adapters (Integration Layer)

- External system communication
- Implement port interfaces
- Wrap libraries (Databricks SDK, subprocess, etc.)

### Models (Data Layer)

- Immutable Pydantic models with `frozen=True`
- Strict validation: `extra="forbid"` rejects unknown/misspelled fields
- Validation via Field constraints and model validators
- No business logic
- `Table.partitioned_by`: optional list of column names for Delta table partitioning (validated against column definitions)

## Usage Examples

### CLI

```bash
# Validate
databricks-contracts validate contract my_table
databricks-contracts validate all

# Apply
databricks-contracts apply contract my_table --env dev --dry-run
databricks-contracts apply contract my_table --env prod

# Trigger
databricks-contracts trigger contracts table1 table2
databricks-contracts trigger modified --base-ref origin/main
databricks-contracts trigger all --dry-run

# Publish to Purview
databricks-contracts publish purview table1 table2
databricks-contracts publish purview table1 --env prod --dry-run
databricks-contracts publish purview-modified --base-ref origin/main
databricks-contracts publish purview-all --env prod
```

### Programmatic

```python
from databricks_contracts.handlers import ApplyHandler, ValidateHandler, PublishHandler
from databricks_contracts.models.inputs import ApplyInput, ValidateInput, PublishInput

# Apply
handler = ApplyHandler.create(environment="prod", dry_run=True)
result = handler.handle(ApplyInput(contract_name="orders"))
print(result.success, result.create_ddl)

# Validate
handler = ValidateHandler.create()
result = handler.handle(ValidateInput(contract_name="orders"))
print(result.valid, result.error)

# Publish to Purview
handler = PublishHandler.create(environment="prod", dry_run=True)
result = handler.handle(PublishInput(contract_name="orders"))
print(result.success, result.purview_qualified_name)

# Publish modified contracts to Purview
handler = PublishHandler.create(environment="prod")
results = handler.handle_modified(base_ref="origin/main")
for result in results:
    print(f"{result.contract_name}: {result.success}")
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABRICKS_HOST` | Workspace URL |
| `DATABRICKS_CLIENT_ID` | Service Principal ID |
| `DATABRICKS_CLIENT_SECRET` | Service Principal Secret |
| `CONTRACTS_PATH` | Path to contracts directory |
| `ENVIRONMENT` | Target environment (dev, prod) |
| `LOG_LEVEL` | Logging level |
| `PURVIEW_ACCOUNT_NAME` | Azure Purview account name |
| `PURVIEW_TENANT_ID` | Azure AD Tenant ID |
| `PURVIEW_CLIENT_ID` | Service Principal Client ID for Purview |
| `PURVIEW_CLIENT_SECRET` | Service Principal Secret for Purview |
| `PURVIEW_QUALIFIED_NAME_PREFIX` | Prefix for qualified names (default: `databricks://`) |
| `PURVIEW_TABLE_TYPE_NAME` | Purview entity type for tables (default: `DataSet`) |
| `PURVIEW_COLUMN_TYPE_NAME` | Purview entity type for columns (default: `column`) |

### Project Config (datacontract.config.yaml)

```yaml
domain:
  name: test_catalog
  sub_domain: test_schema

environments:
  dev:
    catalog_suffix: ""
  prod:
    catalog_suffix: "_prod"
```

## Extending

### Add new command

1. Create `commands/new_command.py`
2. Register in `commands/main.py`:
   ```python
   app.add_typer(new_app, name="new-cmd")
   ```

### Add new executor

1. Implement `BaseExecutor` in `adapters/databricks/executors/`
2. Add to factory in handler

### Add new enum value

1. Update `models/contracts/enums.py`
2. Release new version
