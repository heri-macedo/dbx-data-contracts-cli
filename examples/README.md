# Examples

This folder contains example files for client teams to use as reference.

## Contents

```
examples/
├── data_contracts/             # Default contracts path (matches library default)
│   └── assets/
│       ├── table_name_1.yaml
│       ├── table_name_2.yaml
│       └── table_name_3.yaml
├── templates/                  # Contract templates
│   ├── contract.minimal.yaml   # Minimum required fields
│   └── contract.full.yaml      # All fields including optional
├── resources/                  # DAB Python resources
│   ├── __init__.py             # load_resources() entry point
│   └── scripts/
│       └── main.py             # Job runtime entry point
├── databricks.yaml             # Bundle configuration example
└── datacontract.config.yaml    # Domain configuration (REQUIRED)
```

## Quick Start for Client Teams

### 1. Add the databricks-contracts library

In your `databricks.yaml`, reference the wheel from Unity Catalog Volume:

```yaml
# For DEV environment (latest from develop branch)
libraries:
  - whl: /Volumes/shared/lib/wheels/databricks_contracts-0.0.0.dev0-py3-none-any.whl

# For PROD environment (specific version)
libraries:
  - whl: /Volumes/shared/lib/wheels/databricks_contracts-1.0.0-py3-none-any.whl
```

### 2. Example databricks.yaml for Clients

```yaml
bundle:
  name: my_team_contracts

variables:
  # Choose which version of databricks-contracts to use
  CONTRACTS_WHEEL_PATH:
    description: "Path to databricks-contracts wheel"
    default: "/Volumes/shared/lib/wheels/databricks_contracts-0.0.0.dev0-py3-none-any.whl"

sync:
  include:
    - data_contracts/**
    - datacontract.config.yaml
    - resources/**

resources:
  jobs:
    apply_contracts:
      name: "Apply Data Contracts - ${bundle.target}"
      tasks:
        - task_key: apply_all
          python_wheel_task:
            package_name: databricks_contracts
            entry_point: cli.main:app
            parameters: ["apply", "all", "--env", "${bundle.target}"]
          libraries:
            - whl: ${var.CONTRACTS_WHEEL_PATH}
          new_cluster:
            spark_version: "14.3.x-scala2.12"
            num_workers: 0
            node_type_id: "Standard_DS3_v2"

targets:
  dev:
    default: true
    variables:
      # DEV: Always use latest from develop branch
      CONTRACTS_WHEEL_PATH: "/Volumes/shared/lib/wheels/databricks_contracts-0.0.0.dev0-py3-none-any.whl"

  prod:
    mode: production
    variables:
      # PROD: Use specific version
      CONTRACTS_WHEEL_PATH: "/Volumes/shared/lib/wheels/databricks_contracts-1.0.0-py3-none-any.whl"
```

## Library Versions

| Environment | Wheel Path | Description |
|-------------|------------|-------------|
| **DEV** | `/Volumes/shared/lib/wheels/databricks_contracts-0.0.0.dev0-py3-none-any.whl` | Latest from `develop` branch (auto-updated) |
| **PROD** | `/Volumes/shared/lib/wheels/databricks_contracts-X.Y.Z-py3-none-any.whl` | Specific release version |

## datacontract.config.yaml

This file is **required** in the repository root. It defines:

- **domain.name**: Catalog base name (e.g., `test_catalog`)
- **domain.sub_domain**: Schema name (e.g., `test_schema`)
- **environments.{env}.catalog_suffix**: Suffix per environment

Example catalog resolution:
- `--env dev` → `test_catalog.test_schema.table_name`
- `--env prod` → `test_catalog_prod.test_schema.table_name`

## Testing Locally

To test the CLI with these examples, run from **inside this folder**:

```bash
cd examples

# Validate all contracts
databricks-contracts validate all

# Apply a single contract (dry-run)
databricks-contracts apply contract table_name_1 --dry-run --env dev

# Apply a single contract to prod
databricks-contracts apply contract table_name_1 --env prod

# Trigger all jobs (dry-run)
databricks-contracts trigger all --dry-run

# Publish to Purview (dry-run)
databricks-contracts publish purview table_name_1 --dry-run

# Publish modified contracts to Purview
databricks-contracts publish purview-modified --base-ref origin/main --dry-run
```

## In Databricks Notebook

```python
# Install the library
%pip install /Volumes/shared/lib/wheels/databricks_contracts-0.0.0.dev0-py3-none-any.whl

# Use it (programmatic)
from databricks_contracts.config.project_config_model import load_project_config
from databricks_contracts.services.contracts import BuilderService, ContractLoaderService

loader = ContractLoaderService()
contract = loader.load("table_name_1")

config = load_project_config()
builder = BuilderService(environment="dev", project_config=config)
statements = builder.build(contract)
print(statements[0].statement)
```

## Purview Integration

To publish contracts to Microsoft Purview, configure these environment variables:

| Variable | Description |
|----------|-------------|
| `PURVIEW_ACCOUNT_NAME` | Azure Purview account name |
| `PURVIEW_TENANT_ID` | Azure AD Tenant ID |
| `PURVIEW_CLIENT_ID` | Service Principal Client ID |
| `PURVIEW_CLIENT_SECRET` | Service Principal Secret |

The `ownership.purview_collection` field in contract YAML specifies which Purview collection the entity will be published to.

### CI/CD Integration

Add a step to your GitHub Actions workflow to publish modified contracts:

```yaml
- name: Publish to Purview
  env:
    PURVIEW_ACCOUNT_NAME: ${{ secrets.PURVIEW_ACCOUNT_NAME }}
    PURVIEW_TENANT_ID: ${{ secrets.PURVIEW_TENANT_ID }}
    PURVIEW_CLIENT_ID: ${{ secrets.PURVIEW_CLIENT_ID }}
    PURVIEW_CLIENT_SECRET: ${{ secrets.PURVIEW_CLIENT_SECRET }}
  run: |
    databricks-contracts publish purview-modified \
      --base-ref ${{ github.event.before }} \
      --env ${{ needs.validate.outputs.target }}
```

## Setting Up a New Team Repository

1. Copy `datacontract.config.yaml` and customize for your domain (**required**)
2. Copy `data_contracts/assets/` and add your table contracts
3. Copy `templates/` for contract templates
4. Create your `databricks.yaml` referencing the library from UC Volume
5. (Optional) Copy `resources/` for DAB Python support with dynamic job generation
6. (Optional) Configure Purview secrets for metadata publishing