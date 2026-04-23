# DataGuard - Validation Console

![Python](https://img.shields.io/badge/Python-85.5%25-3776AB?logo=python&logoColor=white)
![T-SQL](https://img.shields.io/badge/T--SQL-14.5%25-CC2927?logo=microsoftsqlserver&logoColor=white)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![SQL Server](https://img.shields.io/badge/DB-SQL%20Server-CC2927?logo=microsoftsqlserver&logoColor=white)
![Status](https://img.shields.io/badge/status-active--development-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

DataGuard is a SQL Server data validation console for finding broken data before it becomes business truth. It combines a Streamlit operations UI, a Python service layer, T-SQL validation functions and procedures, structured validation logs, and run history tables so teams can define rules, execute checks, inspect failures, and trace validation activity from run to log.

---

## Features

- **Japandi Dark Streamlit console** with a restrained operational UI, shared design system, focused navigation, and keyboard-visible focus states.
- **Six-page validation workflow** covering Welcome, Health Dashboard, Run Validations, Results & History, Rule Manager, and Operational Logs.
- **Three-step validation wizard** for selecting table scope, choosing rule execution posture, and confirming a validation run.
- **Dynamic SQL validation execution** through SQL Server procedures and `dbo.vf_*` scalar validation functions.
- **Structured validation logs** stored in `validation_logs` with severity, validation ID, correlation ID, status, payload JSON, exception details, and indexed filtering fields.
- **Live operational log console** with severity filters, minimum severity mode, search, grouped display modes, event details, and copy/filter actions.
- **Per-rule result tracking** in `validation_rule_results`, linked to validation run history for pass/fail rates and duration analysis.
- **Rule Manager** for adding manual rules, accepting suggestions, and reviewing active rulesets against the connected database.
- **SQL Server connection picker** with ODBC driver discovery, Windows authentication, SQL authentication, and database selection.
- **Separated project layers** for pages, reusable components, services, SQL migrations/procedures/functions, utilities, tests, and local setup docs.

---

## Releases

No formal releases have been published yet. Clone `main` for the latest code:

```bash
git clone https://github.com/LSZTM/B1_Training_Project.git
cd B1_Training_Project
```

---

## Usage

### 1. Verify your SQL Server connection

```python
from utils.db import get_available_drivers, test_connection

# Check which SQL Server ODBC drivers are installed.
drivers = get_available_drivers()
print(drivers)
# ['{ODBC Driver 17 for SQL Server}', '{ODBC Driver 18 for SQL Server}']

result = test_connection()
print(result)
# {'success': True, 'driver': '{ODBC Driver 17 for SQL Server}'}
```

### 2. Launch the Streamlit console

```bash
streamlit run main.py
```

DataGuard opens a SQL Server connection screen when no active database is selected. After connection, the app launches into the Welcome page and exposes the full validation console through the sidebar.

### 3. Interpret a validation failure

Validation failures are recorded in run history, rule result tables, error logs, and structured operational logs. A failed validation event includes fields such as severity, validation ID, correlation ID, rule code, validation status, duration, payload JSON, and stack trace when available:

```text
severity: ERROR
event_type: validation.failed
validation_status: FAILED
message: Validation failed for Customers.Email using IsEmail.
correlation_id: 03A0C1A5-BDEF-4913-9F22-2AF91B68745A
```

Use the Operational Logs page to filter by severity, minimum severity, validation ID, rule ID, status, time range, and free-text search.

---

## Validation Rules

| Rule | Description | Example |
|---|---|---|
| `vf_NOT_NULL` | Column value must not be NULL | `FirstName IS NOT NULL` |
| `vf_trimmed` | Text must not contain leading or trailing whitespace | `Name = LTRIM(RTRIM(Name))` |
| `vf_IsEmail` | Text must be a valid email shape | `Email LIKE '%@%.%'` |
| `vf_HasLength` | String length must stay within the configured limit | `LEN(Code) <= 50` |
| `vf_age_range` | Numeric age must fall within the allowed range | `Age BETWEEN 0 AND 150` |
| `vf_date_not_in_future` | Date value must not be later than the current date | `BirthDate <= GETDATE()` |

> Rules are configured through `temp_validation_config` and executed by SQL Server procedures that call matching `dbo.vf_*` validation functions.

---

## API Reference

### `utils.db`

| Function | Returns | Description |
|---|---|---|
| `test_connection()` | `dict` | Attempts a DB handshake and returns connection status details |
| `get_connection()` | `pyodbc.Connection` | Returns an open SQL Server connection for the selected database |
| `get_available_drivers()` | `list[str]` | Lists installed SQL Server-compatible ODBC drivers |
| `discover_server_connection()` | `str` | Builds a server-level connection string for database discovery |
| `list_databases()` | `list[str]` | Lists user databases available on the selected SQL Server instance |
| `switch_database()` | `None` | Updates the active database connection for the Streamlit session |

### `test_connection.py` (legacy helpers)

| Function | Returns | Description |
|---|---|---|
| `get_available_drivers()` | `list[str]` | Filters installed ODBC drivers to SQL Server-compatible options |

### Streamlit Pages (`pages/`)

| Page | Route | Description |
|---|---|---|
| Welcome | `pages/1_Welcome.py` | Product entry point, connection context, and next-step actions |
| Health Dashboard | `pages/2_Dashboard.py` | Validation health, records scanned, failures, and quality charts |
| Run Validations | `pages/3_Execute.py` | Three-step wizard for selecting scope, options, and execution |
| Results & History | `pages/4_History.py` | Run log, error explorer, and quality trend review |
| Rule Manager | `pages/5_Rules.py` | Add suggested/manual rules and inspect the active ruleset |
| Operational Logs | `pages/6_Logs.py` | Live structured log stream with filters and event drill-down |

---

## Contributing

1. **Fork** the repository on GitHub.
2. **Create a branch** for your change:
   ```bash
   git checkout -b feat/your-feature-name
   ```
3. Make your changes, adding tests under `tests/` where applicable.
4. **Open a Pull Request** against `main` with a clear description of what changed and why.

Please keep SQL scalar functions prefixed `dbo.vf_*`, validation orchestration in `services/validation_service.py`, and structured log behavior in `services/logs_service.py` so UI, API, and SQL behavior remain aligned.

---

## Project Status

![Status](https://img.shields.io/badge/status-active--development-yellow)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![SQL Server](https://img.shields.io/badge/SQL%20Server-2019%2B-CC2927)
![Commits](https://img.shields.io/github/commit-activity/m/LSZTM/B1_Training_Project)

Active development. Core validation execution, rule management, structured logging, run history, per-rule result tracking, and the Streamlit console are functional. Current focus areas include hardening SQL migrations, expanding rule coverage, and improving local demo reliability.

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## Support

Open an [issue](https://github.com/LSZTM/B1_Training_Project/issues) on GitHub for bug reports or feature requests. For DB connectivity problems, confirm that **ODBC Driver 17 or 18 for SQL Server** is installed, SQL Server is running, and the selected database is reachable from your machine.
