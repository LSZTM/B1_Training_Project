# Validation Logs: Local Setup and Demo Plan

## What this repo already has

After inspecting the codebase, the current application shape is:

- `main.py`: Streamlit entrypoint, boot loader, and database connection wall.
- `pages/1_Overview.py`, `pages/2_Runs.py`, `pages/3_Errors.py`, `pages/4_Rules.py`: existing dashboard pages.
- `services/validation_service.py`: the main application service layer for validation runs, metrics, errors, and rules.
- `utils/db.py`: SQL Server connection discovery and connection management.
- `sql/migrations`: existing database change scripts.
- `sql/procedures/vp_validate_column.sql`: existing row/rule validation procedure.

That means the clean production-ready implementation path is:

1. Keep SQL Server as the source of truth for log storage.
2. Keep Streamlit as the UI layer.
3. Extend `ValidationService` instead of adding a parallel backend.
4. Store schema changes in `sql/migrations`.
5. Store optional demo data in `sql/seeds`.

## New files added for this feature

- `services/logs_service.py`
- `components/log_workspace.py`
- `pages/5_Logs.py`
- `sql/migrations/20260412_priority5_validation_logs.sql`
- `sql/seeds/20260412_validation_logs_demo_seed.sql`
- `tests/test_logs_service.py`
- `tests/fixtures/validation_logs_fixture.json`

## Database design

### Primary table to create

Create `dbo.validation_logs`.

This table is the structured event stream for the Logs page. It stores:

- event timestamp
- normalized severity
- computed severity rank
- message and event type
- source module
- correlation ID
- validation ID
- validation status
- rule identifiers
- table and column context
- duration
- exception type and stack trace
- structured payload JSON
- input and output summaries

### Why this table exists

The existing schema has:

- `validation_run_history`: run summary history
- `validation_rule_results`: per-rule metrics
- `error_log`: validation failures

Those tables are useful, but they are not enough for a live operational console because they do not provide:

- normalized log levels
- correlation IDs
- a consistent event schema
- structured debugging payloads
- a live append-only event stream

`validation_logs` fills that gap.

### Supporting procedure

Create `dbo.execute_all_validations_with_logging`.

This wrapper:

1. logs `validation.started`
2. calls the existing `dbo.execute_all_validations`
3. reads the new `validation_run_history` rows created by that execution
4. emits structured `validation.passed` and `validation.failed` events
5. emits a final `validation.completed` event
6. writes an `ERROR` event if the batch throws

This lets the Logs page show real lifecycle events instead of reverse-engineering them from history tables after the fact.

## Where to store and run SQL scripts in SSMS

### In the repo

Keep scripts in these folders:

- schema and procedure changes: `sql/migrations`
- optional demo/sample inserts: `sql/seeds`

That matches the existing repo pattern and keeps production schema changes separate from sample data.

### In SSMS

Use this flow:

1. Open SSMS.
2. Connect to the SQL Server instance that backs `QUERY_PRACTICE`.
3. Open a new query window against the `QUERY_PRACTICE` database.
4. Run the scripts in this order:
   - `sql/migrations/20260404_priority1_stub_rule_fix.sql`
   - `sql/migrations/20260404_priority4_validation_rule_results.sql`
   - `sql/migrations/20260412_priority5_validation_logs.sql`
5. If you want demo data immediately, run:
   - `sql/seeds/20260412_validation_logs_demo_seed.sql`

Do not keep the master copy only inside SSMS tabs. Save the authoritative version in the repo under `sql/`.

## What each table does after this change

### `validation_logs`

Operational event stream for the Logs page.

Use it for:

- live monitoring
- severity filtering
- validation journey tracing
- exception inspection
- export and search

### `validation_run_history`

Execution summary history per run or per rule execution result.

Use it for:

- historical run counts
- total scanned rows
- duration
- status trend reporting

### `validation_rule_results`

Per-rule pass/fail metrics for a run.

Use it for:

- run inspector detail
- rule effectiveness reporting
- pass-rate analysis

### `error_log`

Validation failure records already used by the Error Explorer page.

Use it for:

- record-level failure analysis
- field and table error breakdowns

### `temp_validation_config`

Active ruleset configuration.

Use it for:

- rule creation
- rule toggling
- rule execution inputs

## Data flow for the new Logs page

1. User opens `pages/5_Logs.py`.
2. The page reads filter state from Streamlit session state.
3. `services/logs_service.py` queries `dbo.validation_logs`.
4. Summary metrics are computed from the filtered result set.
5. `components/log_workspace.py` renders:
   - live stream pane
   - grouping view
   - detail drawer
   - copy/filter/next/previous actions
6. Clicking row-level quick filters updates Streamlit query parameters.
7. The page consumes those actions and updates session filter state.

## Logging insertion points

### Current insertion points implemented

- `ValidationService.run_all_validations`
- `fetch_df`
- `fetch_value`
- `execute_sql`
- `add_validation_rule`
- `bulk_import_rules`

### Why these are the right seams

- `run_all_validations` is the main batch entrypoint.
- query helper failures are operationally important because they can make the UI look empty or stale.
- rule save/import events are useful for traceability and warnings.

## Production-ready behavior decisions

### Default page behavior

- live mode: on
- auto-scroll: on
- visible severities: `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `DEBUG`: hidden by default
- default range: last hour
- default grouping: flat live stream

### Severity semantics

- `DEBUG`: low-level diagnostics only
- `INFO`: start, completion, pass, normal milestones
- `WARNING`: recoverable issues and degraded behavior
- `ERROR`: failed validations, blocking exceptions
- `CRITICAL`: system-wide or urgent operator attention

### Query and index strategy

The migration adds indexes on:

- event timestamp
- severity rank
- validation ID
- correlation ID
- rule code

That makes the Logs page responsive for:

- recent time windows
- minimum severity filtering
- validation journey drill-down
- correlation tracing
- rule-level filtering

## Local demo plan

### Step 1: prepare SQL Server

Make sure one of the connection strings in `utils/db.py` is valid on your machine:

- `localhost\\SQLEXPRESS`
- `localhost`
- `.`

If your instance name is different, update `WORKING_CONNECTION_STRINGS`.

### Step 2: run the migration scripts

Run:

1. `sql/migrations/20260404_priority1_stub_rule_fix.sql`
2. `sql/migrations/20260404_priority4_validation_rule_results.sql`
3. `sql/migrations/20260412_priority5_validation_logs.sql`

Optional:

4. `sql/seeds/20260412_validation_logs_demo_seed.sql`

### Step 3: start the app locally

From the repo root:

```powershell
streamlit run main.py
```

### Step 4: create live activity

Use one or both of these:

1. Click `Run All Validations` from the existing runs page.
2. Open the new `Validation Logs` page and watch the live stream update.

### Step 5: demo flow

Use this sequence in the demo:

1. Open the Logs page with the default live view.
2. Point out that `DEBUG` is hidden by default.
3. Toggle `Only failures` to isolate high-signal events.
4. Click an `ERROR` or `CRITICAL` row to open structured details.
5. Use `Filter by validation ID` from the details pane.
6. Switch grouping to `Group by validation ID`.
7. Use minimum severity mode and set it to `WARNING`.
8. Export the filtered logs to CSV.

### Step 6: local verification checklist

- page opens without import errors
- summary cards change when filters change
- `DEBUG` does not appear by default
- minimum severity mode expands correctly
- failure-only view removes low-value success logs
- clicking a row opens details
- validation ID quick filter narrows the event journey
- CSV export downloads the filtered set
- live mode refreshes while enabled

## Notes about this local environment

During implementation in this workspace, the SQL Server connection was not reachable from the current machine context, so the feature was built and syntax-checked locally, but not exercised end-to-end against a live database here.

That is why the repo now includes:

- SQL migration scripts
- demo seed data
- unit tests for filtering logic
- a fixture file for repeatable verification

## Commands to verify locally

Syntax check:

```powershell
python -m compileall main.py components pages services utils tests
```

Unit tests:

```powershell
python -m unittest discover -s tests
```
