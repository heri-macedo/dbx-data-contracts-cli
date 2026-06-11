# databricks-contracts

Python library for deploying data contracts to Databricks Unity Catalog and publishing metadata to Microsoft Purview.

## Installation

```bash
# From GitHub
pip install git+https://github.com/your-org/databricks_data_contracts.git@main

# Development (local)
pip install -e .
```

> Setting up a new workspace from scratch (service principal, Unity Catalog grants,
> SQL warehouse, CI/CD secrets)? See [docs/SETUP.md](docs/SETUP.md).

## Quick Start

```bash
# Validate contracts
databricks-contracts validate all
databricks-contracts validate contract test_table

# Apply (dry-run)
databricks-contracts apply contract test_table --dry-run

# Apply (production)
databricks-contracts apply contract test_table --env prod

# Trigger jobs
databricks-contracts trigger contracts test_table --dry-run
databricks-contracts trigger modified --base-ref origin/main
databricks-contracts trigger all --dry-run

# Publish to Purview
databricks-contracts publish purview table_name_1
databricks-contracts publish purview table_name_1 table_name_2 --env prod
databricks-contracts publish purview-modified --base-ref origin/main
databricks-contracts publish purview-all --dry-run
```

## For Teams

This library is meant to be used by team repositories. Use the `examples/` as a starting point for your team's contract repository.

### Creating a Team Repository

1. Copy `examples/` to a new repository
2. Configure `datacontract.config.yaml` with your domain
3. Add contracts to `data_contracts/assets/`
4. Configure GitHub secrets for CI/CD

## Project Structure

```
databricks_contracts/
├── commands/               # CLI layer (Typer)
│   ├── main.py             # Entry point & router
│   ├── apply.py            # apply contract <name>
│   ├── validate.py         # validate contract/all
│   ├── trigger.py          # trigger contracts/modified
│   ├── publish.py          # publish purview/purview-modified/purview-all
│   └── shared/             # Output formatters
│
├── handlers/               # Orchestration layer
│   ├── apply_handler.py    # ApplyHandler
│   ├── validate_handler.py # ValidateHandler
│   ├── trigger_handler.py  # TriggerHandler
│   └── publish_handler.py  # PublishHandler
│
├── services/               # Business logic layer
│   ├── contracts/          # ContractLoaderService, BuilderService
│   ├── git/                # ChangeDetectorService
│   ├── databricks/         # TriggerService
│   ├── purview/            # PurviewPublisherService, ContractToPurviewMapper
│   └── paths/              # PathResolverService
│
├── adapters/               # External integrations
│   ├── databricks/         # DatabricksClient, Executors
│   ├── git/                # SubprocessGitAdapter
│   └── purview/            # PurviewCatalogApiClient, DryRunPurviewClient
│
├── models/                 # Pydantic models (extra="forbid" on all models)
│   ├── contracts/          # Contract, Table, Column, etc.
│   ├── inputs/             # ApplyInput, ValidateInput, PublishInput, etc.
│   ├── results/            # RunResult, TriggerResult, PublishResult, etc.
│   ├── statements/         # CreateTableStatement, TagStatement
│   └── purview/            # PurviewTableEntity, PurviewColumnEntity, etc.
│
├── config/                 # Configuration
│   ├── settings.py         # Environment variables
│   ├── project_config.py   # datacontract.config.yaml
│   └── constants.py        # Constants
│
└── exceptions.py           # Custom exceptions
```

### Test Structure

Tests mirror the source code structure for intuitive navigation:

```
tests/
├── conftest.py                          # Global fixtures (sample_contract_data, etc.)
├── unit/
│   ├── test_models.py                   # General model tests
│   ├── test_services.py                 # General service tests
│   ├── models/
│   │   └── contracts/
│   │       ├── conftest.py              # Fixtures for contract models
│   │       ├── test_table.py            # Table, TableTags (partitioned_by, extra fields)
│   │       ├── test_column.py           # Column, ColumnTags (extra fields)
│   │       ├── test_contract.py         # Contract, ContractInfo (extra fields)
│   │       ├── test_ownership.py        # Ownership (extra fields)
│   │       └── test_source.py           # Source (extra fields)
│   └── services/
│       └── contracts/
│           ├── conftest.py              # Fixtures for builder service
│           └── test_builder.py          # BuilderService (multi-partition DDL)
└── integration/
```

## CLI Commands

```bash
# Validate
databricks-contracts validate contract <name>
databricks-contracts validate all

# Apply
databricks-contracts apply contract <name> --env dev --dry-run
databricks-contracts apply contract <name> --env prod

# Trigger
databricks-contracts trigger contracts <name1> <name2> --dry-run
databricks-contracts trigger modified --base-ref origin/main
databricks-contracts trigger all --dry-run

# Publish to Purview
databricks-contracts publish purview <name1> [name2 ...]
databricks-contracts publish purview <name> --env prod
databricks-contracts publish purview <name> --dry-run
databricks-contracts publish purview-modified --base-ref origin/main
databricks-contracts publish purview-all --env prod

# Utilities
databricks-contracts version
```

## Contract Schema

### Table Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `table.name` | `string` | Yes | Table name (valid SQL identifier) |
| `table.description` | `string` | Yes | Human-readable table description |
| `table.refresh_frequency` | `enum` | Yes | Data refresh frequency |
| `table.retention_days` | `int` | Yes | Data retention period in days |
| `table.tags` | `object` | Yes | Table-level Unity Catalog tags |
| `table.columns` | `list` | Yes | Column definitions (at least one) |
| `table.partitioned_by` | `list[string]` | No | Column names for Delta table partitioning |

The `partitioned_by` field is optional. When specified, all column names must exist in the `columns` list. The generated DDL will include a `PARTITIONED BY` clause:

```sql
CREATE TABLE IF NOT EXISTS `catalog`.`schema`.`table` (
  `order_id` STRING NOT NULL,
  `order_date` DATE NOT NULL
)
USING DELTA
PARTITIONED BY (`order_date`)
```

### Strict Field Validation

All contract models use Pydantic's `extra="forbid"` configuration. This means any unknown or misspelled field in the YAML will cause a validation error instead of being silently ignored.

For example, using `partition_by` (typo) instead of `partitioned_by` will fail:

```
ValidationError: Extra inputs are not permitted [type=extra_forbidden, input_value=['order_date'], input_type=list]
```

This applies to all models: `Contract`, `ContractInfo`, `Table`, `TableTags`, `Column`, `ColumnTags`, `Ownership`, and `Source`.

### Allowed Values (Enums)

| Field | Allowed Values |
|-------|----------------|
| `contract.status` | `draft`, `active`, `deprecated` |
| `table.refresh_frequency` | `realtime`, `hourly`, `daily`, `weekly`, `monthly` |
| `table.tags.layer` | `Admin`, `Bronze`, `Silver`, `Gold` |
| `table.tags.classification` | `Classification_1`, `Classification_2`, `Classification_3`, `Classification_4` (see enums.py) |
| `ownership.portfolio` | `Portfolio_1`, `Portfolio_2`, …, `Portfolio_10` (see enums.py) |
| `ownership.sub_domain` | `Sub_Domain_1`, `Sub_Domain_2`, …, `Sub_Domain_10` (see enums.py) |
| `columns[].tags.privacy` | `PII_HIDDEN`, `PII_ENCRYPTED` |

> **Note**: To add new values, update `databricks_contracts/models/contracts/enums.py`.

## Development

```bash
# Setup
make setup

# Lint & Format
make lint              # Check code style
make format            # Auto-format code

# Tests
make test              # Run all tests
make test-unit         # Run unit tests only
make test-cov          # Tests with coverage

# Clean
make clean
```

## Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI (commands/)                         │
│         apply.py │ validate.py │ trigger.py │ publish.py        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      HANDLERS (handlers/)                       │
│   ApplyHandler │ ValidateHandler │ TriggerHandler │ PublishHandler │
│                     handler.handle(input)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICES (services/)                       │
│   ContractLoaderService │ BuilderService │ TriggerService       │
│   ChangeDetectorService │ PathResolverService │ PurviewPublisher │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ADAPTERS (adapters/)                       │
│  DatabricksClient │ SparkExecutor │ GitAdapter │ PurviewClient  │
└─────────────────────────────────────────────────────────────────┘
```

### CI/CD Flow

```
Developer → git push → GitHub Actions → Validate → Deploy → Publish to Purview

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   develop    │────►│     dev      │────►│ test_catalog │────►│ Purview DEV  │
│   branch     │     │  environment │     │   catalog    │     │  collection  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    main      │────►│     prod     │────►│test_catalog_p│────►│ Purview PROD │
│   branch     │     │  environment │     │   catalog    │     │  collection  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

## Programmatic Usage

```python
from databricks_contracts.handlers import ApplyHandler
from databricks_contracts.models.inputs import ApplyInput

# Create handler with default dependencies
handler = ApplyHandler.create(environment="prod", dry_run=True)

# Execute
result = handler.handle(ApplyInput(contract_name="test_table"))

if result.success:
    print(f"Applied: {result.contract_name}")
    for w in result.warnings:
        print(f"  ⚠ {w}")
else:
    print(f"Error: {result.error}")
```

### Error Handling Strategy

Only the `CREATE TABLE` statement is **fatal**. Tag and grant failures are treated as **non-fatal warnings** so the table is always created even when the executing principal lacks certain tag-policy or grant permissions.

| Step | On failure |
|------|-----------|
| `CREATE TABLE` | **Fatal** — `success=False`, job exits with error |
| `SET TAGS` (one per tag) | **Warning** — collected in `result.warnings`, job succeeds |
| `GRANT` | **Warning** — collected in `result.warnings`, job succeeds |

Tags are applied **one per statement** (`ALTER TABLE SET TAGS ('key' = 'value')`) so that a permission error on one tag (e.g. `classification`) does not block the remaining tags (e.g. `portfolio`, `layer`).

Spark/Py4J error messages are automatically cleaned — only the meaningful message is shown (e.g. `UnauthorizedAccessException: PERMISSION_DENIED: …`) instead of the full Java stack trace.

## Versioning & Releases

### How Versioning Works

Versions are derived **automatically from git tags** using [setuptools-scm](https://github.com/pypa/setuptools-scm). There is no hardcoded version in `pyproject.toml` or source code — the git tag is the single source of truth.

**Tools involved:**

| Tool | Role |
|------|------|
| [setuptools-scm](https://github.com/pypa/setuptools-scm) | Build-time plugin that reads git tags and computes the package version. Configured in `pyproject.toml` under `[tool.setuptools_scm]`. |
| `SETUPTOOLS_SCM_PRETEND_VERSION` | Environment variable that overrides setuptools-scm. Used in CI to force a stable dev version. |
| `importlib.metadata` | Python stdlib. `__init__.py` reads the installed package version at runtime — no generated files needed. |

**How the version is resolved:**

```
git tag v1.2.0          ← you create a tag
  │
  ├─ on-release.yml     → setuptools-scm sees HEAD == v1.2.0 → version = "1.2.0"
  │
  └─ on-push.yml (develop)
       → LAST_TAG = v1.2.0
       → SETUPTOOLS_SCM_PRETEND_VERSION = "1.2.0.dev0"
       → version = "1.2.0.dev0" (fixed until next tag)
```

**Version table:**

| Workflow | Trigger | How version is set | Example version | Wheel name |
|----------|---------|-------------------|-----------------|------------|
| `on-push` | Push to `develop` | Last git tag + `.dev0` via `SETUPTOOLS_SCM_PRETEND_VERSION` | `1.2.0.dev0` | `databricks_contracts-1.2.0.dev0-py3-none-any.whl` |
| `on-push` | Push to `main` | No wheel built (lint, test, validate only) | — | — |
| `on-release` | Tag `v1.2.0` | setuptools-scm reads the tag directly | `1.2.0` | `databricks_contracts-1.2.0-py3-none-any.whl` |

The dev wheel (`X.Y.Z.dev0`) is **overwritten on every push to develop** — there is no accumulation of dev versions. It changes automatically when a new tag is created.

### Configuration Reference

Three files make the versioning system work:

#### 1. `pyproject.toml` — build-time configuration

```toml
[project]
name = "databricks-contracts"
dynamic = ["version"]            # ← version is NOT hardcoded

[build-system]
requires = ["setuptools>=61.0", "wheel", "setuptools-scm>=8"]
build-backend = "setuptools.build_meta"

[tool.setuptools_scm]
version_scheme = "guess-next-dev"  # after v1.2.0, non-tagged → 1.2.1.devN
local_scheme = "no-local-version"  # no +g<hash> suffix (PEP 440 clean)
tag_regex = "^v(?P<version>\\d+\\.\\d+\\.\\d+)$"  # matches v1.2.0
```

- `dynamic = ["version"]` tells setuptools to delegate version resolution to a plugin instead of using a static value.
- `setuptools-scm>=8` in `build-system.requires` ensures the plugin is available during `python -m build`.
- `version_scheme = "guess-next-dev"` means: if HEAD is exactly on `v1.2.0`, the version is `1.2.0`; otherwise it computes the next patch + `.devN`.
- `local_scheme = "no-local-version"` removes the `+g<hash>` local part that would make the version non-PEP 440 compliant for uploads.

#### 2. `databricks_contracts/__init__.py` — runtime version

```python
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("databricks-contracts")
except PackageNotFoundError:
    __version__ = "0.0.0"
```

This reads the version from the installed package metadata (written by setuptools-scm at build time). No source file is modified — `importlib.metadata` reads from `*.dist-info/METADATA`.

#### 3. CI workflows — version override for dev builds

In `on-push.yml`, the dev build step calculates the version from the latest tag:

```yaml
- name: Set dev version
  run: |
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
    BASE_VERSION=${LAST_TAG#v}
    echo "SETUPTOOLS_SCM_PRETEND_VERSION=${BASE_VERSION}.dev0" >> $GITHUB_ENV

- name: Build wheel
  run: python -m build --wheel
```

The version is set via `$GITHUB_ENV` so it persists across all subsequent steps in the job (including `databricks bundle deploy`, which also rebuilds the wheel internally). This guarantees a stable, fixed `X.Y.Z.dev0` filename that gets overwritten on each push.

In `on-release.yml`, no override is needed — setuptools-scm reads the tag directly from `HEAD`:

```yaml
- name: Build wheel
  run: python -m build --wheel
  # HEAD == v1.2.0 → version = "1.2.0"
```

### Wheel Storage Location

Wheels are published to a **Unity Catalog Volume**:

```
dbfs:/Volumes/shared/lib/wheels/
├── databricks_contracts-1.2.0.dev0-py3-none-any.whl  # Dev (overwritten on each push to develop)
├── databricks_contracts-1.2.0-py3-none-any.whl       # Versioned release
├── databricks_contracts-1.3.0-py3-none-any.whl       # Versioned release
└── databricks_contracts-latest-py3-none-any.whl      # Alias to latest release
```

### Creating a Release (Production)

```bash
# 1. Create and push a tag
git tag v1.2.0
git push origin main --tags

# 2. The on-release.yml workflow will:
#    - Build wheel with version 1.2.0 (from setuptools-scm)
#    - Deploy bundle to prod
#    - Publish wheel to UC Volume (versioned + "latest" alias)
#    - Create GitHub Release with install instructions
#
# 3. After the release, dev builds automatically become 1.2.0.dev0
```

### Using the Library in Subdomain Repos

#### In Databricks Jobs (databricks.yml)

```yaml
# Use specific version (recommended for prod)
libraries:
  - whl: /Volumes/shared/lib/wheels/databricks_contracts-1.2.0-py3-none-any.whl

# Or use latest release
libraries:
  - whl: /Volumes/shared/lib/wheels/databricks_contracts-latest-py3-none-any.whl

# Or use dev version (for testing — always the latest develop build)
libraries:
  - whl: /Volumes/shared/lib/wheels/databricks_contracts-1.2.0.dev0-py3-none-any.whl
```

#### In Databricks Notebook

```python
# Install specific version
%pip install /Volumes/shared/lib/wheels/databricks_contracts-1.2.0-py3-none-any.whl

# Or latest
%pip install /Volumes/shared/lib/wheels/databricks_contracts-latest-py3-none-any.whl
```

#### Via pip (local development)

```bash
# From GitHub tag
pip install git+https://github.com/your-org/databricks-data-contracts.git@v1.2.0

# From GitHub main (dev)
pip install git+https://github.com/your-org/databricks-data-contracts.git@main
```

> **Private repositories and client setup:** Installations of the library from private repositories must be configured by each client. The flow described here assumes `pip install` via GitHub; access to the library repository must be set up so that subdomain (or team) repos can download the library. For private repositories or restricted networks, evaluate and adapt the subdomain workflow (e.g. authentication, CI secrets, or installing from an internal artifact store instead of the Git host).

### Checking Installed Version

```bash
# Via CLI
databricks-contracts version

# Via pip
pip show databricks-contracts
```

## Purview Integration

### Overview

The library publishes data contracts as entities to Microsoft Purview using custom types:

| Contract Element | Purview Entity Type |
|-----------------|---------------------|
| Table | `databricks_table` |
| Column | `databricks_table_column` |

### Entity Mapping

#### Table Attributes

| Contract Field | Purview Attribute |
|---------------|-------------------|
| `table.name` | `name` |
| `table.description` | `comment` |
| `catalog` | `catalogName` |
| `schema` | `schemaName` |

#### Table Tags (stored in `tags` map)

| Contract Field | Purview Tag Key |
|---------------|-----------------|
| `ownership.portfolio` | `portfolio` |
| `ownership.sub_domain` | `sub_domain` |
| `ownership.data_owner` | `data_owner` |
| `ownership.bds` | `bds` |
| `ownership.tds` | `tds` |
| `contract.version` | `contract_version` |
| `table.tags.layer` | `layer` |
| `table.tags.classification` | `classification` |
| `table.refresh_frequency` | `refresh_frequency` |
| `table.retention_days` | `retention_days` |

#### Column Attributes

| Contract Field | Purview Attribute |
|---------------|-------------------|
| `column.name` | `name` |
| `column.type` | `dataType` |
| `column.nullable` | `isNullable` |
| `column.description` | `comment` |
| Position in array | `ordinalPosition` |

#### Column Privacy Tags → Classifications

Privacy tags are mapped to **Purview Classifications** (not tags):

| Contract `columns[].tags.privacy` | Purview Classification |
|----------------------------------|------------------------|
| `PII_HIDDEN` | `PII_HIDDEN` |
| `PII_ENCRYPTED` | `PII_ENCRYPTED` |

> ⚠️ **Important**: These classifications must be created manually in Purview before use.
> Go to **Data Map → Classifications → + New** and create `PII_HIDDEN` and `PII_ENCRYPTED`.

### Collection Fallback

If the collection specified in `ownership.purview_collection` doesn't exist in Purview, the entity will be published to the **root collection** with a warning:

```
Collection 'NonExistentCollection' not found in Purview. Falling back to root collection 'account-name'
```

The output will show:
```
│ my_contract │ ✅ │ account-name (root) │ databricks://metastore/... │
```

### Limitations

#### Classifications are NOT automatically removed

When you **remove** a privacy tag from a column in your contract and republish, the classification will **NOT** be removed from Purview. This is a Purview API behavior (merge, not replace).

**To remove a classification:**
- Manually via Purview UI: Entity → Classifications → Delete


---

## GitHub CI/CD Configuration

### Repository Types

| Repository | Description |
|------------|-------------|
| **Library repo** (`databricks-data-contracts`) | This library. Contains the CLI and core logic. |
| **Domain repos** (e.g., `data-contracts-sales`) | Team repositories that use this library. |

### Library Repository Secrets

No secrets needed for the library itself (it's a package).

### Domain Repository Configuration

Each domain/subdomain repository that uses this library needs:

#### 1. GitHub Secrets (Settings → Secrets → Actions)

| Secret | Description | Example |
|--------|-------------|---------|
| `DATABRICKS_HOST` | Databricks workspace URL | `https://adb-123.azuredatabricks.net` |
| `DATABRICKS_CLIENT_ID` | Service Principal App ID | `12345678-1234-...` |
| `DATABRICKS_CLIENT_SECRET` | Service Principal Secret | `xxxxxxxx` |
| `PURVIEW_ACCOUNT_NAME` | Purview account name | `my-purview-account` |
| `PURVIEW_TENANT_ID` | Azure AD Tenant ID | `12345678-1234-...` |
| `PURVIEW_CLIENT_ID` | Service Principal App ID for Purview | `12345678-1234-...` |
| `PURVIEW_CLIENT_SECRET` | Service Principal Secret for Purview | `xxxxxxxx` |

#### 2. GitHub Workflow (`.github/workflows/deploy.yml`)

```yaml
name: Deploy Data Contracts

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install git+https://github.com/your-org/databricks-data-contracts.git@main
      
      - name: Validate all contracts
        run: databricks-contracts validate all

  deploy-dev:
    if: github.ref == 'refs/heads/develop'
    needs: validate
    runs-on: ubuntu-latest
    environment: dev
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Needed for modified detection
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install git+https://github.com/your-org/databricks-data-contracts.git@main
      
      - name: Deploy modified contracts
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID }}
          DATABRICKS_CLIENT_SECRET: ${{ secrets.DATABRICKS_CLIENT_SECRET }}
        run: |
          databricks-contracts trigger modified --base-ref origin/main --env dev
      
      - name: Publish to Purview
        env:
          PURVIEW_ACCOUNT_NAME: ${{ secrets.PURVIEW_ACCOUNT_NAME }}
          PURVIEW_TENANT_ID: ${{ secrets.PURVIEW_TENANT_ID }}
          PURVIEW_CLIENT_ID: ${{ secrets.PURVIEW_CLIENT_ID }}
          PURVIEW_CLIENT_SECRET: ${{ secrets.PURVIEW_CLIENT_SECRET }}
        run: |
          databricks-contracts publish purview-modified --base-ref origin/main --env dev

  deploy-prod:
    if: github.ref == 'refs/heads/main'
    needs: validate
    runs-on: ubuntu-latest
    environment: prod
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install git+https://github.com/your-org/databricks-data-contracts.git@main
      
      - name: Deploy modified contracts
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST_PROD }}
          DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID_PROD }}
          DATABRICKS_CLIENT_SECRET: ${{ secrets.DATABRICKS_CLIENT_SECRET_PROD }}
        run: |
          databricks-contracts trigger modified --base-ref origin/main --env prod
      
      - name: Publish to Purview
        env:
          PURVIEW_ACCOUNT_NAME: ${{ secrets.PURVIEW_ACCOUNT_NAME }}
          PURVIEW_TENANT_ID: ${{ secrets.PURVIEW_TENANT_ID }}
          PURVIEW_CLIENT_ID: ${{ secrets.PURVIEW_CLIENT_ID_PROD }}
          PURVIEW_CLIENT_SECRET: ${{ secrets.PURVIEW_CLIENT_SECRET_PROD }}
        run: |
          databricks-contracts publish purview-modified --base-ref origin/main --env prod
```

#### 3. Repository Structure

```
data-contracts-my-domain/        # Domain repository
├── .github/
│   └── workflows/
│       └── deploy.yml           # CI/CD workflow
├── data_contracts/
│   ├── assets/
│   │   ├── table_name_1.yaml    # Contract files
│   │   ├── table_name_2.yaml
│   │   └── ...
│   └── datacontract.config.yaml # Domain configuration
├── .env.example                 # Example environment variables
└── README.md
```

#### 4. Domain Configuration (`datacontract.config.yaml`)

```yaml
# Domain identification (required)
domain:
  name: "my_catalog"                   # Catalog base (Unity Catalog)
  sub_domain: "my_schema"              # Schema (Unity Catalog)
  description: "My Domain"            # Description for documentation
```

#### 5. Databricks Bundle Configuration (`databricks.yml`)

> ⚠️ **IMPORTANT**: Each subdomain must have a **unique bundle name** to avoid conflicts!

If two subdomains use the same bundle name in different repos, their resources (jobs, workflows) will **overwrite each other** during deployment.

**Naming Convention:**

```yaml
# ❌ BAD - Generic name causes conflicts
bundle:
  name: data_contracts

# ✅ GOOD - Include subdomain in bundle name
bundle:
  name: data_contracts_sales
```

| Subdomain | Bundle Name |
|-----------|-------------|
| Sales | `data_contracts_sales` |
| Finance | `data_contracts_finance` |
| Marketing | `data_contracts_marketing` |
| Operations | `data_contracts_operations` |

**Example `databricks.yml`:**

```yaml
bundle:
  name: data_contracts_sales  # Unique per subdomain!

workspace:
  host: ${DATABRICKS_HOST}

targets:
  dev:
    mode: development
    default: true

  prod:
    mode: production
    workspace:
      root_path: /Workspace/.bundle/${bundle.name}/prod
```

**What the bundle name affects:**

| Resource | Impact |
|----------|--------|
| Jobs | Job names include bundle name |
| Workspace paths | `/Workspace/.bundle/{bundle_name}/` |
| State files | Bundle state stored per name |
| Permissions | Applied to bundle-named resources |

### Dynamic Job Generation

The library **dynamically generates Databricks jobs** by reading all YAML contract files from `data_contracts/assets/`:

```
data_contracts/
└── assets/
    ├── table_name_1.yaml  →  Job: "apply_table_name_1"
    ├── table_name_2.yaml  →  Job: "apply_table_name_2"
    └── table_name_3.yaml  →  Job: "apply_table_name_3"
```

**How it works:**

1. During `databricks bundle deploy`, the library scans `data_contracts/assets/*.yaml`
2. For each contract file, it generates a Databricks job definition

**Example generated job:**

| Contract File | Generated Job Name |
|---------------|-------------------|
| `nyc_taxi_daily_summary.yaml` | `[dev dc] Apply Contract - nyc_taxi_daily_summary` |
| `customers.yaml` | `[dev dc] Apply Contract - customers` |

> **Note**: You don't need to manually define jobs in `databricks.yml`. The library handles job generation automatically based on your contract files.

### Azure Permissions Required

#### Databricks Service Principal (Library Repo)

The library repo publishes wheels to a **shared Unity Catalog Volume**. Both DEV and PROD Service Principals need access to this shared location:

| Permission | Resource | Why |
|------------|----------|-----|
| `READ_VOLUME` | `/Volumes/shared/lib/wheels` | Read wheel files |
| `WRITE_VOLUME` | `/Volumes/shared/lib/wheels` | Publish wheel files |
| `USE CATALOG` | `shared` | Access shared catalog |
| `USE SCHEMA` | `shared.lib` | Access lib schema |

```sql
-- Grant permissions to Service Principals (run as admin)
GRANT USE CATALOG ON CATALOG shared TO `sp-databricks-dev`;
GRANT USE CATALOG ON CATALOG shared TO `sp-databricks-prod`;

GRANT USE SCHEMA ON SCHEMA shared.lib TO `sp-databricks-dev`;
GRANT USE SCHEMA ON SCHEMA shared.lib TO `sp-databricks-prod`;

GRANT READ VOLUME, WRITE VOLUME ON VOLUME shared.lib.wheels TO `sp-databricks-dev`;
GRANT READ VOLUME, WRITE VOLUME ON VOLUME shared.lib.wheels TO `sp-databricks-prod`;
```

> ⚠️ **Important**: Both DEV and PROD Service Principals must have **identical permissions** on the shared volume, as the CI/CD pipeline publishes wheels from both environments.

#### Databricks Service Principal (Subdomain Repos)

Each subdomain repo deploys contracts to its own catalog. The Service Principal needs:

| Permission | Resource | Why |
|------------|----------|-----|
| `USE CATALOG` | Domain catalog (e.g., `sales_dev`) | Access catalog |
| `USE SCHEMA` | Domain schema | Access schema |
| `CREATE TABLE` | Domain schema | Create tables |
| `MODIFY` | Domain schema | Alter tables |
| `READ VOLUME` | `/Volumes/shared/lib/wheels` | Install library |

```sql
-- Grant permissions for subdomain (example: sales)
GRANT USE CATALOG ON CATALOG sales_dev TO `sp-databricks-dev`;
GRANT USE SCHEMA ON SCHEMA sales_dev.contracts TO `sp-databricks-dev`;
GRANT CREATE TABLE, MODIFY ON SCHEMA sales_dev.contracts TO `sp-databricks-dev`;

-- Also needs read access to shared lib volume
GRANT READ VOLUME ON VOLUME shared.lib.wheels TO `sp-databricks-dev`;
```

#### Purview Service Principal

- **Data Curator** role on the Purview account
- Access to create/update entities in the target collections

---

## Documentation

- [Library Architecture](databricks_contracts/README.md)
