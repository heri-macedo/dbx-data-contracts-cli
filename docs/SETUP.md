# Setup from Zero

End-to-end guide to enable the CLI in a new Databricks workspace: service principal,
Unity Catalog permissions, SQL warehouse access, and GitHub secrets for CI/CD.

## Architecture recap

Two repositories work together:

- **CLI repo** (this one): the `databricks-contracts` library. Merges to `develop`/`main`
  build and deploy the library into the dev/prod workspace. Nothing is executed against
  tables at this point.
- **Template repo** (team contract repos): holds the contract YAMLs and the DAB bundle.
  Its CI/jobs are what actually run `apply` and create/evolve tables — on Databricks
  jobs (Spark) using the service principal below.

## 1. Create the service principal

In the target workspace (Admin Settings → Identity and access → Service principals):

1. Create a service principal (e.g. `data-contracts-sp`).
2. Generate an **OAuth secret** for it (Client ID + Secret). These map to:
   - `DATABRICKS_CLIENT_ID` / `DATABRICKS_CLIENT_SECRET` at runtime
   - `DATABRICKS_SP_CLIENT_ID_{DEV,PROD}` / `DATABRICKS_SP_SECRET_{DEV,PROD}` as GitHub secrets

## 2. Unity Catalog permissions

The CLI executes the following statements, all against the catalog/schema resolved from
`datacontract.config.yaml` (`domain.name` + `environments.{env}.catalog_suffix` /
`domain.sub_domain`):

| Operation | Statement | Required privilege |
|---|---|---|
| Create tables | `CREATE TABLE IF NOT EXISTS` | `USE CATALOG`, `USE SCHEMA`, `CREATE TABLE` |
| Schema evolution | `ALTER TABLE ADD COLUMNS / ALTER COLUMN / ADD CONSTRAINT` | `MODIFY` (or table ownership) |
| Introspection | `DESCRIBE TABLE EXTENDED`, `SHOW TBLPROPERTIES` | `SELECT` (or `BROWSE`) |
| Tagging | `ALTER TABLE ... SET TAGS` | `APPLY TAG` |
| Grants | `GRANT MODIFY ON TABLE` | table ownership (the SP owns tables it creates) or `MANAGE` |

Simplest setup — grant everything at the catalog level:

```sql
GRANT ALL PRIVILEGES ON CATALOG <catalog_dev> TO `<sp-application-id>`;
```

`ALL PRIVILEGES` covers all rows in the table above except `GRANT`, which works because
the SP becomes **owner** of every table it creates.

For a least-privilege setup instead:

```sql
GRANT USE CATALOG ON CATALOG <catalog_dev> TO `<sp-application-id>`;
GRANT USE SCHEMA, CREATE TABLE, SELECT, MODIFY, APPLY TAG
  ON SCHEMA <catalog_dev>.<schema> TO `<sp-application-id>`;
```

> **Tag policies:** if the workspace enforces governed tags, the SP also needs permission
> on each tag policy. Tag failures are non-fatal (collected as warnings in `RunResult`).

## 3. SQL warehouse access (table introspection)

Outside a Spark runtime (local CLI, GitHub runner), schema evolution depends on the
Statement Execution API, which requires:

- `DATABRICKS_WAREHOUSE_ID` set in the environment, and
- the SP having **CAN USE** on that warehouse (SQL Warehouses → Permissions).

**If `DATABRICKS_WAREHOUSE_ID` is not set, the inspector silently reports the table as
non-existing and `apply` always takes the creation path** (`CREATE TABLE IF NOT EXISTS`
— harmless, but no `ALTER` is ever generated). On Databricks jobs (Spark) the inspector
uses the local Spark session and no warehouse is needed.

## 4. GitHub secrets (CI/CD)

The workflows in `.github/workflows/` consume:

| Secret | Used by |
|---|---|
| `DATABRICKS_HOST_DEV`, `DATABRICKS_SP_CLIENT_ID_DEV`, `DATABRICKS_SP_SECRET_DEV` | pushes to `develop` |
| `DATABRICKS_HOST_PROD`, `DATABRICKS_SP_CLIENT_ID_PROD`, `DATABRICKS_SP_SECRET_PROD` | pushes to `main`, releases |

Populate them with the helper script (uses `gh` CLI):

```bash
cp scripts/.secrets.env.example scripts/.secrets.env   # fill in the values
./scripts/update-secrets.sh -e dev -f scripts/.secrets.env    # only *_DEV
./scripts/update-secrets.sh -e prod -f scripts/.secrets.env   # only *_PROD
./scripts/update-secrets.sh -f scripts/.secrets.env           # everything
```

If your git remote uses an SSH host alias, point `gh` at the right repo explicitly:

```bash
GH_REPO=<org>/<repo> ./scripts/update-secrets.sh -e dev -f scripts/.secrets.env
```

## 5. Validate the setup

Quickest end-to-end check — run the apply in dry-run with the SP credentials exported:

```bash
export DATABRICKS_HOST=...
export DATABRICKS_CLIENT_ID=...
export DATABRICKS_CLIENT_SECRET=...
export DATABRICKS_WAREHOUSE_ID=...   # optional, enables evolution detection
databricks-contracts apply --all --dry-run
```

Or verify grants directly:

```sql
SHOW GRANTS `<sp-application-id>` ON CATALOG <catalog_dev>;
```
