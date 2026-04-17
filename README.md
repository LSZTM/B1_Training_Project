# DataGuard — Validation Console

![Python](https://img.shields.io/badge/Python-85.5%25-3776AB?logo=python&logoColor=white)
![T-SQL](https://img.shields.io/badge/T--SQL-14.5%25-CC2927?logo=microsoftsqlserver&logoColor=white)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![SQL Server](https://img.shields.io/badge/DB-SQL%20Server-CC2927?logo=microsoftsqlserver&logoColor=white)
![Status](https://img.shields.io/badge/status-active--development-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

A full-stack data quality and validation framework for SQL Server tables. DataGuard combines a Python `ValidationService` orchestration layer, T-SQL scalar functions and a dynamic dispatcher stored procedure, and a Streamlit web console — giving teams a single interface to define, run, and monitor column-level validation rules.

---

## Features

- **Animated boot screen** with step-by-step startup sequence and live DB handshake; falls back to a retry wall on connection failure.
- **Dynamic SQL dispatcher** (`vp_validate_column`) routes each rule to the correct scalar validation function (`dbo.vf_*`) at runtime.
- **Per-rule result tracking** stored in `validation_rule_results` — every execution is persisted with pass/fail status and timestamp.
- **Error rate trend panel** surfaces historical error rates per column/rule over time.
- **Unified DB connection layer** (`utils.db`) with auto-discovery of available ODBC drivers via `pyodbc`.
- **Error code alignment** between `error_code_master` and `error_log` to prevent silent reporting corruption.
- **Multi-page Streamlit UI** (`pages/`) with a shared sidebar component and custom CSS design system (`utils/styles.py`).
- **Structured validation logging** — all failures captured to `validation.log` with ODBC error codes (e.g. `42S22`).
- **Component/service separation** — UI components, service layer, SQL, utilities, and tests live in clearly separated directories.

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
from utils.db import test_connection, get_available_drivers

# Check which ODBC drivers are installed
drivers = get_available_drivers()
print(drivers)
# ['ODBC Driver 17 for SQL Server', 'ODBC Driver 18 for SQL Server']

result = test_connection()
print(result)
# {'success': True, 'driver': 'ODBC Driver 17 for SQL Server'}
```

### 2. Launch the Streamlit console

```bash
streamlit run main.py
```

DataGuard boots, runs its DB handshake against `QUERY_PRACTICE`, and redirects to the Overview page. If the connection fails, a retry screen is shown rather than a crash.

### 3. Interpret a validation failure

When a rule references an invalid column, the `ValidationService` catches the ODBC error and writes to `validation.log`:

```
ERROR:services.validation_service:Validation failed: ('42S22',
"[42S22] [Microsoft][ODBC Driver 17 for SQL Server][SQL Server]
Invalid column name 'FIrstNameS'. (207) (SQLExecDirectW)")
```

The error code `42S22` maps to `error_code_master` for human-readable reporting in the UI.

---

## Validation Rules

| Rule | Description | Example |
|---|---|---|
| `vf_not_null` | Column value must not be NULL | `FirstName IS NOT NULL` |
| `vf_max_length` | String length must not exceed a threshold | `LEN(Email) <= 255` |
| `vf_numeric_range` | Numeric value must fall within min/max bounds | `Age BETWEEN 0 AND 150` |
| `vf_regex_match` | Value must match a regular expression pattern | `PostCode LIKE '[A-Z][0-9]%'` |
| `vf_referential` | Foreign key value must exist in a reference table | `CountryCode IN (SELECT Code FROM Countries)` |
| `vf_date_format` | Date column must be a valid, parseable date | `ISDATE(BirthDate) = 1` |

> Rules are dispatched dynamically by `vp_validate_column` — adding a new `dbo.vf_*` scalar function automatically makes it available to the dispatcher.

---

## API Reference

### `utils.db`

| Function | Returns | Description |
|---|---|---|
| `test_connection()` | `dict` | Attempts a DB handshake; returns `{'success': bool, 'driver': str}` |
| `get_connection()` | `pyodbc.Connection` | Returns an open connection using the discovered driver |
| `discover_working_connection_string()` | `str` | Iterates available ODBC drivers and returns the first working DSN |
| `close_connection(conn)` | `None` | Safely closes an open connection |

### `test_connection.py` (legacy helpers)

| Function | Returns | Description |
|---|---|---|
| `get_available_drivers()` | `list[str]` | Filters `pyodbc.drivers()` to SQL Server-compatible drivers |

### Streamlit Pages (`pages/`)

| Page | Route | Description |
|---|---|---|
| Overview | `pages/1_Overview.py` | Entry point; summary dashboard |
| Rules | `pages/Rules.py` | Define and manage validation rules |
| Results | `pages/Results.py` | Per-rule pass/fail history and error rate trends |

---

## Contributing

1. **Fork** the repository on GitHub.
2. **Create a branch** for your change:
   ```bash
   git checkout -b feat/your-feature-name
   ```
3. Make your changes, adding tests under `tests/` where applicable.
4. **Open a Pull Request** against `main` with a clear description of what changed and why.

Please keep SQL scalar functions prefixed `dbo.vf_*` and service methods in `services/validation_service.py` to maintain the dispatcher contract.

---

## Project Status

![Status](https://img.shields.io/badge/status-active--development-yellow)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![SQL Server](https://img.shields.io/badge/SQL%20Server-2019%2B-CC2927)
![Commits](https://img.shields.io/github/commit-activity/m/LSZTM/B1_Training_Project)

Active development. Core validation pipeline, DB layer, and Streamlit UI are functional. Rule health metrics (P7) and canonical `Rule` object (P3) are in progress.

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## Support

Open an [issue](https://github.com/LSZTM/B1_Training_Project/issues) on GitHub for bug reports or feature requests. For DB connectivity problems, confirm that **ODBC Driver 17 (or 18) for SQL Server** is installed on your machine and that the `QUERY_PRACTICE` server is reachable from your host.
