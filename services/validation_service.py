import base64
import json
import logging
import re
import uuid
from contextlib import contextmanager

import pandas as pd

from services.logs_service import LogsService
from services.rule import Rule
from utils.db import close_connection, get_connection

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, filename="validation.log")


@contextmanager
def db_conn():
    """Context manager for DB connection."""
    conn = get_connection()
    try:
        yield conn
    finally:
        if conn:
            close_connection(conn)


def fetch_df(query, params=None):
    """Return query results as DataFrame."""
    try:
        with db_conn() as conn:
            return pd.read_sql(query, conn, params=params)
    except Exception as e:
        logger.error("fetch_df failed: %s", e)
        LogsService.capture_exception(
            message="DataFrame query failed",
            source_module="services.validation_service.fetch_df",
            exception=e,
            payload={"query": query, "params": params},
            event_type="validation.query.failed",
            validation_status=None,
        )
        return pd.DataFrame()


def fetch_value(query, params=None, default=0):
    """Return single value from query."""
    try:
        with db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            row = cursor.fetchone()
            return row[0] if row else default
    except Exception as e:
        logger.error("fetch_value failed: %s", e)
        LogsService.capture_exception(
            message="Scalar query failed",
            source_module="services.validation_service.fetch_value",
            exception=e,
            payload={"query": query, "params": params},
            event_type="validation.query.failed",
            validation_status=None,
        )
        return default


def execute_sql(query, params=None):
    """Execute SQL command."""
    try:
        with db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            conn.commit()
            return True
    except Exception as e:
        logger.error("execute_sql failed: %s", e)
        LogsService.capture_exception(
            message="SQL execution failed",
            source_module="services.validation_service.execute_sql",
            exception=e,
            payload={"query": query, "params": params},
            event_type="validation.command.failed",
            validation_status=None,
        )
        return False


class ValidationService:
    NOT_IMPLEMENTED_RULES = set()
    NUMERIC_TYPES = {
        "int", "bigint", "smallint", "tinyint", "decimal", "numeric", "float", "real", "money", "smallmoney"
    }
    STRING_TYPES = {"varchar", "nvarchar", "char", "nchar", "text", "ntext"}
    DATE_TYPES = {"date", "datetime", "datetime2", "smalldatetime", "timestamp", "time"}

    RULE_SIGNAL_MAP: dict[str, dict] = {
        # TYPE
        "NOT_NULL": {"keywords": ["required", "mandatory", "id", "key"], "data_types": ["*"], "detector": None, "category": "type", "description": "Column must not be null.", "base_conf": 0.82},
        "is_digit": {"keywords": ["id", "qty", "count", "number"], "data_types": ["int", "bigint", "smallint", "tinyint"], "detector": None, "category": "type", "description": "Whole number type validation.", "base_conf": 0.85},
        "is_decimal": {"keywords": ["amount", "price", "cost", "sum", "total"], "data_types": ["decimal", "numeric", "float", "real", "money"], "detector": None, "category": "type", "description": "Decimal numeric validation.", "base_conf": 0.84},
        "is_boolean": {"keywords": ["is_", "flag", "active", "enabled", "should"], "data_types": ["bit", "bool"], "detector": r"^(0|1|true|false|yes|no|t|f)$", "category": "type", "description": "Boolean domain validation.", "base_conf": 0.82},
        "is_integer_string": {"keywords": ["id", "code", "number", "ref"], "data_types": ["varchar", "char"], "detector": r"^-?\d+$", "category": "type", "description": "String that should contain integer text.", "base_conf": 0.76},
        # FORMAT
        "IsEmail": {"keywords": ["email", "mail", "contact"], "data_types": ["varchar", "nvarchar"], "detector": r"^(?=.{1,254}$)(?=.{1,64}@)[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$", "category": "format", "description": "Email address format.", "base_conf": 0.88},
        "is_phone_e164": {"keywords": ["phone", "mobile", "tel", "sms"], "data_types": ["varchar", "nvarchar"], "detector": r"^\+[1-9]\d{7,14}$", "category": "format", "description": "E.164 phone format.", "base_conf": 0.82},
        "is_phone_us": {"keywords": ["phone", "mobile", "tel", "office"], "data_types": ["varchar", "nvarchar"], "detector": r"^(\(\d{3}\))?[\s-]?\d{3}[\s-]?\d{4}$", "category": "format", "description": "US phone format.", "base_conf": 0.8},
        "IsDate": {"keywords": ["date", "dob", "birth", "day"], "data_types": ["date", "datetime", "varchar"], "detector": r"^\d{4}-\d{2}-\d{2}$", "category": "format", "description": "Date string format.", "base_conf": 0.84},
        "is_datetime": {"keywords": ["time", "timestamp", "created", "updated", "at"], "data_types": ["datetime", "datetime2", "varchar"], "detector": r"^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}(:\d{2})?$", "category": "format", "description": "Datetime format.", "base_conf": 0.83},
        "is_time": {"keywords": ["time", "hour", "minute"], "data_types": ["time", "varchar"], "detector": r"^\d{2}:\d{2}(:\d{2})?$", "category": "format", "description": "Time format.", "base_conf": 0.8},
        "is_uuid": {"keywords": ["uuid", "guid", "id", "sid"], "data_types": ["varchar", "char"], "detector": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", "category": "format", "description": "UUID format.", "base_conf": 0.88},
        "is_ssn": {"keywords": ["ssn", "social", "taxid"], "data_types": ["varchar", "char"], "detector": r"^\d{3}-\d{2}-\d{4}$", "category": "format", "description": "US SSN format.", "base_conf": 0.82},
        "is_postal_code_us": {"keywords": ["zip", "postal"], "data_types": ["varchar", "char"], "detector": r"^\d{5}(-\d{4})?$", "category": "format", "description": "US postal code.", "base_conf": 0.78},
        "is_ip_v4": {"keywords": ["ip", "ipv4", "host", "address"], "data_types": ["varchar", "nvarchar"], "detector": r"^(\d{1,3}\.){3}\d{1,3}$", "category": "format", "description": "IPv4 format.", "base_conf": 0.77},
        "is_url": {"keywords": ["url", "link", "website", "uri", "endpoint"], "data_types": ["varchar", "nvarchar"], "detector": r"^https?://[^\s/$.?#].[^\s]*$", "category": "format", "description": "HTTP/HTTPS URL.", "base_conf": 0.8},
        "is_json": {"keywords": ["json", "payload", "metadata", "config", "data"], "data_types": ["varchar", "nvarchar", "text"], "structural": "json", "category": "format", "description": "Valid JSON payload.", "base_conf": 0.85},
        "is_base64": {"keywords": ["base64", "blob", "encoded", "file"], "data_types": ["varchar", "nvarchar"], "structural": "base64", "category": "format", "description": "Base64 text.", "base_conf": 0.75},
        # RANGE
        "min_value": {"keywords": ["min", "lower", "start", "from"], "data_types": ["int", "bigint", "decimal", "float"], "category": "range", "description": "Lower bound from sample p05.", "base_conf": 0.82},
        "max_value": {"keywords": ["max", "upper", "end", "to"], "data_types": ["int", "bigint", "decimal", "float"], "category": "range", "description": "Upper bound from sample p95.", "base_conf": 0.82},
        "positive_only": {"keywords": ["price", "amount", "salary", "qty", "age", "balance"], "data_types": ["int", "decimal", "float", "money"], "category": "range", "description": "Values should be non-negative.", "base_conf": 0.84},
        "percentage_range": {"keywords": ["rate", "pct", "percent", "ratio"], "data_types": ["decimal", "numeric", "float", "real"], "category": "range", "description": "Percentage range 0-100.", "base_conf": 0.84},
        # LENGTH & INTEGRITY
        "HasLength": {"keywords": ["name", "desc", "text", "code"], "data_types": ["varchar", "nvarchar", "char", "text"], "category": "integrity", "description": "Max length aligns with schema.", "base_conf": 0.88},
        "min_length": {"keywords": ["code", "key", "id", "ref"], "data_types": ["varchar", "nvarchar"], "category": "integrity", "description": "Minimum practical string length.", "base_conf": 0.76},
        "exact_length": {"keywords": ["code", "id", "ssn"], "data_types": ["char"], "category": "integrity", "description": "Fixed width CHAR length.", "base_conf": 0.88},
        "is_in_list": {"keywords": ["status", "type", "category"], "data_types": ["*"], "category": "integrity", "description": "Allowed value list.", "base_conf": 0.84},
        "is_unique": {"keywords": ["id", "key", "code", "ref", "uuid", "guid"], "data_types": ["*"], "category": "integrity", "description": "Values should be unique.", "base_conf": 0.83},
        "ColumnComparison": {"keywords": ["start", "end", "from", "to", "min", "max"], "data_types": ["*"], "category": "integrity", "description": "Compare with another column.", "base_conf": 0.68},
        "foreign_key_check": {"keywords": ["_id", "_fk", "ref"], "data_types": ["int", "varchar"], "category": "integrity", "description": "Foreign key existence check.", "base_conf": 0.72},
        # HYGIENE
        "no_sql_injection": {"keywords": ["comment", "note", "text", "query", "desc"], "data_types": ["varchar", "nvarchar", "text"], "category": "hygiene", "description": "Block SQL injection patterns.", "base_conf": 0.76},
        "no_html_tags": {"keywords": ["comment", "note", "text", "body", "html"], "data_types": ["varchar", "nvarchar", "text"], "category": "hygiene", "description": "Block HTML tags.", "base_conf": 0.75},
        "trimmed": {"keywords": ["name", "code", "ref", "text"], "data_types": ["varchar", "nvarchar", "text"], "category": "hygiene", "description": "Composite trim rule.", "base_conf": 0.74},
        "encoding_check": {"keywords": ["text", "desc", "comment"], "data_types": ["varchar", "nvarchar", "text"], "category": "hygiene", "description": "Detect encoding anomalies.", "base_conf": 0.7},
        # BUSINESS & SECURITY
        "luhn_check": {"keywords": ["card", "credit", "debit", "pan"], "data_types": ["varchar", "char"], "category": "business", "description": "Luhn checksum.", "base_conf": 0.82},
        "iban_checksum": {"keywords": ["iban", "bank", "account"], "data_types": ["varchar", "char"], "category": "business", "description": "IBAN mod-97 checksum.", "base_conf": 0.82},
        "email_domain_whitelist": {"keywords": ["email", "mail"], "data_types": ["varchar", "nvarchar"], "category": "business", "description": "Email domain whitelist.", "base_conf": 0.68},
        "date_not_weekend": {"keywords": ["business", "trading", "working"], "data_types": ["date", "datetime"], "category": "business", "description": "Date must not be weekend.", "base_conf": 0.72},
        "date_not_holiday": {"keywords": ["business", "trading", "working"], "data_types": ["date", "datetime"], "category": "business", "description": "Date must not be holiday.", "base_conf": 0.68},
        "non_overlapping_range": {"keywords": ["start", "end"], "data_types": ["date", "datetime"], "category": "business", "description": "Ranges should not overlap.", "base_conf": 0.66},
        "positive_balance": {"keywords": ["balance", "credit", "debit"], "data_types": ["decimal", "money"], "category": "business", "description": "Balance should be non-negative.", "base_conf": 0.8},
        "gender_code": {"keywords": ["gender", "sex"], "data_types": ["varchar", "char"], "category": "business", "description": "Gender code domain.", "base_conf": 0.86},
        "no_pii_pattern": {"keywords": ["note", "comment", "text", "bio"], "data_types": ["varchar", "nvarchar", "text"], "category": "security", "description": "Block PII patterns in free text.", "base_conf": 0.8},
        "masked_value": {"keywords": ["password", "secret", "token", "key", "hash", "pwd"], "data_types": ["varchar", "char"], "category": "security", "description": "Value should appear masked.", "base_conf": 0.74},
        "no_cleartext_password": {"keywords": ["password", "pwd", "passwd", "secret"], "data_types": ["varchar", "nvarchar"], "category": "security", "description": "Block cleartext password-like values.", "base_conf": 0.88},
    }

    @staticmethod
    def _get_table_columns(table_name: str) -> set[str]:
        df = fetch_df(
            """
            SELECT LOWER(COLUMN_NAME) AS column_name
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            """,
            [table_name],
        )
        return set(df["column_name"].tolist()) if not df.empty else set()

    def _is_safe_identifier(value):
        return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value or ""))

    @staticmethod
    def _quote_identifier(value):
        return f"[{value}]"

    @staticmethod
    def _upsert_suggestion(bucket, rule_code, rule_params, confidence, rationale, source, category):
        entry = {
            "rule_code": rule_code,
            "rule_params": rule_params or "",
            "confidence": round(float(max(0.0, min(0.99, confidence))), 2),
            "rationale": rationale,
            "source": source,
            "category": category,
        }
        current = bucket.get(rule_code)
        if not current or entry["confidence"] > current["confidence"]:
            bucket[rule_code] = entry
        elif current["rationale"] != rationale:
            current["rationale"] = f"{current['rationale']} | {rationale}"

    @staticmethod
    def run_all_validations(table_filter=None):
        correlation_id = str(uuid.uuid4())
        validation_id = str(uuid.uuid4())
        LogsService.log_event(
            severity="INFO",
            message="Validation batch started.",
            event_type="validation.started",
            source_module="services.validation_service.run_all_validations",
            validation_id=validation_id,
            correlation_id=correlation_id,
            validation_status="STARTED",
            payload={"procedure": "dbo.execute_all_validations_with_logging"},
        )
        try:
            with db_conn() as conn:
                cursor = conn.cursor()
                used_wrapper = False

                try:
                    cursor.execute("EXEC dbo.execute_all_validations_with_logging @table_filter=?", [table_filter])
                    row = cursor.fetchone()
                    conn.commit()
                    used_wrapper = True
                except Exception as wrapper_error:
                    if "execute_all_validations_with_logging" not in str(wrapper_error):
                        raise

                    cursor.execute("EXEC dbo.execute_all_validations @table_filter=?", [table_filter])
                    conn.commit()
                    cursor.execute(
                        """
                        SELECT TOP 1 run_id, total_records_scanned, total_errors, duration_ms, status
                        FROM validation_run_history
                        ORDER BY run_id DESC
                        """
                    )
                    fallback = cursor.fetchone()
                    if not fallback:
                        row = None
                    else:
                        row = (
                            validation_id,
                            correlation_id,
                            fallback[0],
                            1,
                            1 if (fallback[2] or 0) > 0 else 0,
                            fallback[1],
                            fallback[2],
                            fallback[3],
                            fallback[4],
                        )

                if not row:
                    LogsService.log_event(
                        severity="WARNING",
                        message="Validation batch completed without any run history rows.",
                        event_type="validation.completed",
                        source_module="services.validation_service.run_all_validations",
                        validation_id=validation_id,
                        correlation_id=correlation_id,
                        validation_status="COMPLETED",
                        payload={"used_wrapper": used_wrapper, "run_rows": 0},
                    )
                    return {"success": True, "validation_id": validation_id, "correlation_id": correlation_id}

                result = {
                    "success": True,
                    "validation_id": str(row[0] or validation_id),
                    "correlation_id": str(row[1] or correlation_id),
                    "run_id": row[2],
                    "run_count": row[3],
                    "failed_runs": row[4],
                    "records_scanned": row[5],
                    "total_errors": row[6],
                    "duration_ms": row[7],
                    "status": row[8],
                }

            LogsService.log_event(
                severity="INFO",
                message="Validation batch completed.",
                event_type="validation.completed",
                source_module="services.validation_service.run_all_validations",
                validation_id=result["validation_id"],
                correlation_id=result["correlation_id"],
                validation_status="COMPLETED",
                duration_ms=result.get("duration_ms"),
                output_summary=result,
                payload={"failed_runs": result.get("failed_runs", 0), "run_count": result.get("run_count", 0)},
            )
            return result
        except Exception as e:
            logger.error("run_all_validations failed: %s", e)
            LogsService.capture_exception(
                message="Validation batch failed.",
                source_module="services.validation_service.run_all_validations",
                exception=e,
                event_type="validation.failed",
                validation_id=validation_id,
                correlation_id=correlation_id,
                payload={"procedure": "dbo.execute_all_validations_with_logging"},
            )
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_run_history(limit=100):
        columns = ValidationService._get_table_columns("validation_run_history")
        if not columns:
            return pd.DataFrame()
        select_parts = [
            "run_id" if "run_id" in columns else "CAST(NULL AS INT) AS run_id",
            "table_name" if "table_name" in columns else "CAST(NULL AS NVARCHAR(128)) AS table_name",
            "column_name" if "column_name" in columns else "CAST(NULL AS NVARCHAR(128)) AS column_name",
            "rule_code" if "rule_code" in columns else "CAST(NULL AS NVARCHAR(64)) AS rule_code",
            "total_records_scanned" if "total_records_scanned" in columns else "CAST(0 AS INT) AS total_records_scanned",
            "total_errors" if "total_errors" in columns else "CAST(0 AS INT) AS total_errors",
            "duration_ms" if "duration_ms" in columns else "CAST(0 AS INT) AS duration_ms",
            "status" if "status" in columns else "CAST('unknown' AS NVARCHAR(32)) AS status",
            "run_timestamp" if "run_timestamp" in columns else "GETDATE() AS run_timestamp",
        ]
        return fetch_df(
            f"""
            SELECT TOP (?) {", ".join(select_parts)}
            FROM validation_run_history
            ORDER BY run_id DESC
            """,
            [limit],
        )

    @staticmethod
    def get_run_details(run_id):
        df = fetch_df(
            """
            SELECT TOP 1 run_id, table_name, column_name, rule_code, total_records_scanned, total_errors, duration_ms, status, run_timestamp
            FROM validation_run_history
            WHERE run_id = ?
            """,
            [run_id],
        )
        if df.empty:
            return {}
        row = df.iloc[0]
        return {
            "run_id": int(row.get("run_id", 0)),
            "table_name": row.get("table_name"),
            "column_name": row.get("column_name"),
            "rule_code": row.get("rule_code"),
            "records_scanned": int(row.get("total_records_scanned", 0) or 0),
            "total_errors": int(row.get("total_errors", 0) or 0),
            "duration_ms": int(row.get("duration_ms", 0) or 0),
            "status": str(row.get("status", "unknown")).lower(),
            "run_timestamp": str(row.get("run_timestamp")),
        }

    @staticmethod
    def get_rule_results(run_id):
        if not ValidationService._get_table_columns("validation_rule_results"):
            return pd.DataFrame()
        return fetch_df(
            """
            SELECT result_id, run_id, table_name, column_name, rule_code, rows_scanned, pass_count, fail_count, pass_rate, run_timestamp
            FROM dbo.validation_rule_results
            WHERE run_id = ?
            ORDER BY result_id ASC
            """,
            [run_id],
        )

    @staticmethod
    def get_metrics():
        try:
            rules = fetch_value("SELECT COUNT(*) FROM temp_validation_config WHERE is_active = 1")
            codes = fetch_value("SELECT COUNT(*) FROM error_code_master")
            errors = fetch_value("SELECT COUNT(*) FROM error_log")
            recent = fetch_df(
                """
                SELECT TOP 1 total_errors, total_records_scanned,
                       DATEDIFF(MINUTE, run_timestamp, GETDATE()) AS minutes_ago
                FROM validation_run_history
                ORDER BY run_id DESC
                """
            )
            row = recent.iloc[0] if not recent.empty else None
            return {
                "rules": rules,
                "codes": codes,
                "errors": errors,
                "records_scanned": row["total_records_scanned"] if row is not None else 0,
                "recent_errors": row["total_errors"] if row is not None else 0,
                "minutes_ago": row["minutes_ago"] if row is not None else 0,
            }
        except Exception as e:
            logger.error("get_metrics failed: %s", e)
            return {"rules": 0, "codes": 0, "errors": 0}

    @staticmethod
    def get_error_trend(days=14) -> pd.DataFrame:
        return fetch_df(
            """
            SELECT
                run_timestamp,
                total_errors,
                total_records_scanned,
                CAST(
                    CASE
                        WHEN ISNULL(total_records_scanned, 0) = 0 THEN 0
                        ELSE (CASE WHEN 1.0 * total_errors / total_records_scanned > 1.0 THEN 1.0 ELSE 1.0 * total_errors / total_records_scanned END)
                    END
                    AS DECIMAL(10,4)
                ) AS error_rate
            FROM validation_run_history
            WHERE run_timestamp >= DATEADD(DAY, -?, GETDATE())
            ORDER BY run_timestamp ASC
            """,
            [int(days)],
        )

    @staticmethod
    def get_recent_errors(limit=10):
        return fetch_df("""SELECT TOP (?) table_name, record_identifier, failed_field, error_code, log_time FROM error_log ORDER BY log_time DESC""", [limit])

    @staticmethod
    def get_error_summary_by_table():
        return fetch_df("""SELECT table_name, COUNT(*) AS error_count, COUNT(DISTINCT record_identifier) AS affected_records FROM error_log GROUP BY table_name ORDER BY error_count DESC""")

    @staticmethod
    def get_tables():
        df = fetch_df("SELECT DISTINCT table_name FROM error_log ORDER BY table_name")
        return df["table_name"].tolist() if not df.empty else []

    @staticmethod
    def get_columns(table_name=None):
        if table_name:
            df = fetch_df("SELECT DISTINCT failed_field FROM error_log WHERE table_name = ? ORDER BY failed_field", [table_name])
        else:
            df = fetch_df("SELECT DISTINCT failed_field FROM error_log ORDER BY failed_field")
        return df["failed_field"].tolist() if not df.empty else []

    @staticmethod
    def get_error_codes():
        df = fetch_df(
            """
            SELECT error_code FROM error_code_master
            UNION
            SELECT DISTINCT error_code FROM error_log
            ORDER BY 1
            """
        )
        return df["error_code"].tolist() if not df.empty else []

    @staticmethod
    def get_error_code_reference():
        return fetch_df(
            """
            SELECT c.error_code, m.description
            FROM (
                SELECT error_code FROM error_code_master
                UNION
                SELECT DISTINCT error_code FROM error_log
            ) c
            LEFT JOIN error_code_master m
                ON c.error_code = m.error_code
            ORDER BY c.error_code
            """
        )

    @staticmethod
    def get_filtered_errors(table=None, column=None, error_code=None, limit=500):
        query = """
        SELECT TOP (?) e.table_name, e.record_identifier, e.failed_field, e.error_code, m.description AS error_description, e.log_time
        FROM error_log e
        LEFT JOIN error_code_master m ON e.error_code = m.error_code
        WHERE 1=1
        """
        params = [limit]
        if table:
            query += " AND e.table_name = ?"
            params.append(table)
        if column:
            query += " AND e.failed_field = ?"
            params.append(column)
        if error_code:
            query += " AND e.error_code = ?"
            params.append(error_code)
        query += " ORDER BY e.log_time DESC"
        return fetch_df(query, params)

    @staticmethod
    def clear_error_log():
        return execute_sql("TRUNCATE TABLE error_log")

    @staticmethod
    def get_rule_implementation_map():
        status_map = {code: True for code in ValidationService.RULE_SIGNAL_MAP.keys()}
        for code in ValidationService.NOT_IMPLEMENTED_RULES:
            status_map[code] = False

        if not ValidationService._get_table_columns("rule_implementation_status"):
            return status_map
        df = fetch_df("SELECT rule_code, is_implemented FROM dbo.rule_implementation_status")
        if not df.empty:
            for _, row in df.iterrows():
                status_map[str(row["rule_code"])] = bool(row["is_implemented"])
        return status_map

    @staticmethod
    def get_active_rules():
        columns = ValidationService._get_table_columns("temp_validation_config")
        if not columns:
            return pd.DataFrame()
        select_parts = [
            "ROW_NUMBER() OVER (ORDER BY table_name, column_name, rule_code) AS id",
            "table_name",
            "column_name",
            "rule_code",
            "rule_params" if "rule_params" in columns else "CAST(NULL AS NVARCHAR(4000)) AS rule_params",
            "allow_null" if "allow_null" in columns else "CAST(0 AS BIT) AS allow_null",
            "is_active" if "is_active" in columns else "CAST(1 AS BIT) AS is_active",
            "error_code" if "error_code" in columns else "CAST('E000' AS NVARCHAR(16)) AS error_code",
            "comparison_column" if "comparison_column" in columns else "CAST(NULL AS NVARCHAR(128)) AS comparison_column",
        ]
        return fetch_df(f"""SELECT {", ".join(select_parts)} FROM temp_validation_config ORDER BY table_name, column_name""")

    @staticmethod
    def get_validation_rules():
        return ValidationService.get_active_rules()

    @staticmethod
    def toggle_rule(rule_id, is_active):
        if "is_active" not in ValidationService._get_table_columns("temp_validation_config"):
            return False
        return False

    @staticmethod
    def delete_rule(rule_id):
        return False

    @staticmethod
    def _ensure_error_code_registered(error_code: str, description: str = None):
        """Ensures an error code exists in error_code_master with a friendly description."""
        if not error_code:
            return
        try:
            exists = fetch_value("SELECT COUNT(*) FROM dbo.error_code_master WHERE error_code = ?", [error_code])
            if not exists:
                desc = description or f"Validation failed for code: {error_code}"
                execute_sql(
                    "INSERT INTO dbo.error_code_master (error_code, description, table_scope) VALUES (?, ?, 'B')",
                    [error_code, desc[:255]]
                )
                logger.info("Registered new error code in master table: %s", error_code)
        except Exception as e:
            logger.error("Failed to register error code %s: %s", error_code, e)

    @staticmethod
    def add_validation_rule(rule_or_table, column=None, rule_code=None, rule_params="", allow_null=False, is_active=True, error_code="E000", comparison_column=None):
        if isinstance(rule_or_table, Rule):
            rule = rule_or_table
        else:
            implementation_map = ValidationService.get_rule_implementation_map()
            rule = Rule.from_signal_map(
                table=rule_or_table,
                column=column,
                rule_code=rule_code,
                rule_signal_map=ValidationService.RULE_SIGNAL_MAP,
                implementation_map=implementation_map,
                rule_params=rule_params,
                allow_null=allow_null,
                is_active=is_active,
                error_code=error_code,
                comparison_column=comparison_column,
            )

        if rule.rule_code in ValidationService.NOT_IMPLEMENTED_RULES:
            logger.warning("Rejected add_validation_rule for not implemented rule: %s", rule.rule_code)
            LogsService.log_event(
                severity="WARNING",
                message=f"Attempted to save not-yet-implemented rule {rule.rule_code}.",
                event_type="validation.rule.skipped",
                source_module="services.validation_service.add_validation_rule",
                validation_context=f"{rule.table}.{rule.column}",
                rule_code=rule.rule_code,
                table_name=rule.table,
                column_name=rule.column,
                payload={"error_code": rule.error_code},
            )
            return False

        # Register code in master table if missing
        ValidationService._ensure_error_code_registered(
            rule.error_code, 
            ValidationService.RULE_SIGNAL_MAP.get(rule.rule_code, {}).get("description")
        )

        try:
            with db_conn() as conn:
                cursor = conn.cursor()
                columns = ValidationService._get_table_columns("temp_validation_config")
                duplicate_count = fetch_value(
                    """
                    SELECT COUNT(*)
                    FROM dbo.temp_validation_config
                    WHERE table_name = ? AND column_name = ? AND rule_code = ?
                    """,
                    [rule.table, rule.column, rule.rule_code],
                    default=0,
                )

                if duplicate_count:
                    update_clauses = []
                    update_values = []
                    updatable_mapping = [
                        ("rule_params", rule.rule_params),
                        ("allow_null", int(rule.allow_null)),
                        ("is_active", int(rule.is_active)),
                        ("error_code", rule.error_code),
                        ("comparison_column", rule.comparison_column),
                    ]
                    for column_name, value in updatable_mapping:
                        if column_name in columns:
                            update_clauses.append(f"{column_name} = ?")
                            update_values.append(value)
                    if update_clauses:
                        cursor.execute(
                            f"""
                            UPDATE dbo.temp_validation_config
                            SET {", ".join(update_clauses)}
                            WHERE table_name = ? AND column_name = ? AND rule_code = ?
                            """,
                            *update_values,
                            rule.table,
                            rule.column,
                            rule.rule_code,
                        )
                        conn.commit()
                    LogsService.log_event(
                        severity="INFO",
                        message=f"Validation rule {rule.rule_code} already existed and was updated.",
                        event_type="validation.rule.updated",
                        source_module="services.validation_service.add_validation_rule",
                        validation_context=f"{rule.table}.{rule.column}",
                        rule_code=rule.rule_code,
                        table_name=rule.table,
                        column_name=rule.column,
                        payload={
                            "rule_params": rule.rule_params,
                            "allow_null": rule.allow_null,
                            "is_active": rule.is_active,
                            "error_code": rule.error_code,
                            "comparison_column": rule.comparison_column,
                        },
                    )
                    return True

                insert_columns = []
                insert_values = []

                mapping = [
                    ("table_name", rule.table),
                    ("column_name", rule.column),
                    ("rule_code", rule.rule_code),
                    ("rule_params", rule.rule_params),
                    ("allow_null", int(rule.allow_null)),
                    ("is_active", int(rule.is_active)),
                    ("error_code", rule.error_code),
                    ("comparison_column", rule.comparison_column),
                ]
                for column_name, value in mapping:
                    if column_name in columns:
                        insert_columns.append(column_name)
                        insert_values.append(value)

                placeholders = ", ".join("?" for _ in insert_columns)
                cursor.execute(
                    f"""
                    INSERT INTO dbo.temp_validation_config
                    ({", ".join(insert_columns)})
                    VALUES ({placeholders})
                    """,
                    *insert_values,
                )
                conn.commit()
                LogsService.log_event(
                    severity="INFO",
                    message=f"Validation rule {rule.rule_code} saved.",
                    event_type="validation.rule.saved",
                    source_module="services.validation_service.add_validation_rule",
                    validation_context=f"{rule.table}.{rule.column}",
                    rule_code=rule.rule_code,
                    table_name=rule.table,
                    column_name=rule.column,
                    payload={
                        "rule_params": rule.rule_params,
                        "allow_null": rule.allow_null,
                        "is_active": rule.is_active,
                        "error_code": rule.error_code,
                        "comparison_column": rule.comparison_column,
                    },
                )
                return True
        except Exception as e:
            logger.error("add_validation_rule failed: %s", e)
            LogsService.capture_exception(
                message="Saving validation rule failed.",
                source_module="services.validation_service.add_validation_rule",
                exception=e,
                event_type="validation.rule.failed",
                payload={
                    "table": getattr(rule, "table", rule_or_table),
                    "column": getattr(rule, "column", column),
                    "rule_code": getattr(rule, "rule_code", rule_code),
                },
            )
            return False

    @staticmethod
    def bulk_import_rules(df):
        success = 0
        try:
            with db_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("TRUNCATE TABLE dbo.temp_validation_config")
                columns = ValidationService._get_table_columns("temp_validation_config")
                for _, row in df.iterrows():
                    try:
                        insert_columns = []
                        insert_values = []
                        mapping = [
                            ("table_name", row["table_name"]),
                            ("column_name", row["column_name"]),
                            ("rule_code", row["rule_code"]),
                            ("rule_params", row.get("rule_params")),
                            ("allow_null", int(row.get("allow_null", 0))),
                            ("is_active", 1),
                            ("error_code", row.get("error_code", "E000")),
                        ]
                        for column_name, value in mapping:
                            if column_name in columns:
                                insert_columns.append(column_name)
                                insert_values.append(value)
                        placeholders = ", ".join("?" for _ in insert_columns)
                        cursor.execute(
                            f"""
                            INSERT INTO dbo.temp_validation_config
                            ({", ".join(insert_columns)})
                            VALUES ({placeholders})
                            """,
                            *insert_values,
                        )
                        success += 1
                    except Exception:
                        continue
                conn.commit()
        except Exception as e:
            logger.error("bulk_import_rules failed: %s", e)
            LogsService.capture_exception(
                message="Bulk rule import failed.",
                source_module="services.validation_service.bulk_import_rules",
                exception=e,
                event_type="validation.rule.import.failed",
                payload={"row_count": len(df) if hasattr(df, "__len__") else None},
            )
        return success

    @staticmethod
    def get_db_tables():
        df = fetch_df("""SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME""")
        return df["TABLE_NAME"].tolist() if not df.empty else []

    @staticmethod
    def get_table_columns(table):
        df = fetch_df("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ? ORDER BY COLUMN_NAME", [table])
        return df["COLUMN_NAME"].tolist() if not df.empty else []

    @staticmethod
    def get_table_schema(table):
        return fetch_df(
            """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
            """,
            [table],
        )

    @staticmethod
    def _fetch_non_null_sample(table: str, column: str, target: int = 150, max_scan: int = 3000) -> pd.DataFrame:
        try:
            scan = int(max(1, min(max_scan, max(target, 1))))
            query = (
                f"SELECT TOP ({scan}) {ValidationService._quote_identifier(column)} AS sample_value "
                f"FROM {ValidationService._quote_identifier(table)} "
                f"WHERE {ValidationService._quote_identifier(column)} IS NOT NULL"
            )
            df = fetch_df(query)
            if df.empty:
                return pd.DataFrame(columns=["sample_value"])
            return df.head(target)
        except Exception as e:
            logger.error("_fetch_non_null_sample failed: %s", e)
            return pd.DataFrame(columns=["sample_value"])

    @staticmethod
    def _fetch_null_rate(table: str, column: str) -> float:
        try:
            query = (
                f"SELECT CAST(SUM(CASE WHEN {ValidationService._quote_identifier(column)} IS NULL THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(*),0) "
                f"FROM {ValidationService._quote_identifier(table)}"
            )
            return round(float(fetch_value(query, default=0.0) or 0.0), 4)
        except Exception as e:
            logger.error("_fetch_null_rate failed: %s", e)
            return 0.0

    @staticmethod
    def _compute_string_length_stats(series: pd.Series) -> dict:
        if series.empty:
            return {"min": 0, "p05": 0, "p50": 0, "p95": 0, "max": 0, "avg": 0}
        lens = series.astype(str).str.len()
        return {
            "min": int(lens.min()),
            "p05": float(lens.quantile(0.05)),
            "p50": float(lens.quantile(0.50)),
            "p95": float(lens.quantile(0.95)),
            "max": int(lens.max()),
            "avg": float(lens.mean()),
        }

    @staticmethod
    def _detect_structural_pattern(series: pd.Series, structural_type: str) -> float:
        if series.empty:
            return 0.0
        vals = series.dropna().astype(str).str.strip()
        if vals.empty:
            return 0.0
        
        ok = 0
        for v in vals:
            try:
                if structural_type == "json":
                    json.loads(v)
                    ok += 1
                elif structural_type == "base64":
                    if len(v) % 4 == 0 and re.match(r"^[A-Za-z0-9+/]+={0,2}$", v):
                        base64.b64decode(v, validate=True)
                        ok += 1
            except Exception:
                pass
        return round(ok / len(vals), 4)

    @staticmethod
    def _calculate_sample_entropy(series: pd.Series) -> float:
        import math
        if series.empty:
            return 0.0
        text = "".join(series.dropna().astype(str))
        if not text:
            return 0.0
        counts = {}
        for char in text:
            counts[char] = counts.get(char, 0) + 1
        probs = [c / len(text) for c in counts.values()]
        return -sum(p * math.log2(p) for p in probs)

    @staticmethod
    def _get_char_profile(series: pd.Series) -> dict:
        if series.empty:
            return {"digit": 0, "alpha": 0, "symbol": 0, "space": 0}
        text = "".join(series.dropna().astype(str))
        if not text:
            return {"digit": 0, "alpha": 0, "symbol": 0, "space": 0}
        total = len(text)
        return {
            "digit": round(sum(c.isdigit() for c in text) / total, 4),
            "alpha": round(sum(c.isalpha() for c in text) / total, 4),
            "symbol": round(sum(not c.isalnum() and not c.isspace() for c in text) / total, 4),
            "space": round(sum(c.isspace() for c in text) / total, 4),
        }

    @staticmethod
    def _detect_case_pattern(series: pd.Series) -> str:
        vals = series.dropna().astype(str).str.strip()
        if vals.empty:
            return "mixed"
        if all(v.isupper() for v in vals if v.isalpha()):
            return "upper"
        if all(v.islower() for v in vals if v.isalpha()):
            return "lower"
        if all(v.istitle() for v in vals if v.isalpha()):
            return "title"
        # Check for camelCase or snake_case
        if all(re.match(r"^[a-z]+([A-Z][a-z]+)*$", v) for v in vals if v):
            return "camel"
        if all(re.match(r"^[a-z]+(_[a-z]+)*$", v) for v in vals if v):
            return "snake"
        return "mixed"

    @staticmethod
    def _classify_column(data_type: str, null_rate: float, non_null_sample: pd.Series, detectors: dict[str, str]) -> dict:
        values = non_null_sample.dropna().astype(str).str.strip()
        fingerprint = {}
        
        # Pattern signals
        for key, pattern in detectors.items():
            try:
                fingerprint[key] = round(float(values.str.match(pattern, na=False).mean()) if len(values) else 0.0, 4)
            except re.error:
                fingerprint[key] = 0.0
        
        # Statistical signals
        entropy = ValidationService._calculate_sample_entropy(values)
        profile = ValidationService._get_char_profile(values)
        case_pattern = ValidationService._detect_case_pattern(values)
        
        top_pattern = max(fingerprint, key=fingerprint.get) if fingerprint else None
        top_match_rate = fingerprint.get(top_pattern, 0.0) if top_pattern else 0.0
        unique_ratio = float(values.nunique() / max(len(values), 1))
        avg_length = float(values.str.len().mean()) if len(values) else 0.0

        if null_rate >= 0.90:
            category = "sparse"
        elif data_type in ValidationService.STRING_TYPES and avg_length > 40 and top_match_rate < 0.35:
            category = "free_text"
        elif top_match_rate >= 0.80:
            category = "typed"
        elif entropy > 4.5 and profile["symbol"] > 0.1:
            category = "mixed" # likely encrypted or high-entropy tokens
        elif top_match_rate >= 0.40:
            category = "mixed"
        else:
            category = "opaque"

        return {
            "category": category,
            "fingerprint": fingerprint,
            "top_pattern": top_pattern,
            "top_match_rate": round(float(top_match_rate), 4),
            "unique_ratio": round(unique_ratio, 4),
            "avg_length": round(avg_length, 2),
            "null_rate": round(float(null_rate), 4),
            "entropy": round(entropy, 2),
            "char_profile": profile,
            "case_pattern": case_pattern,
        }

    @staticmethod
    def _get_context_warning(category, fingerprint, null_rate):
        if category == "sparse":
            return f"Sparse column ({null_rate:.0%} NULL)."
        if category == "free_text":
            return "Free-text fingerprint; hygiene/security-first suggestions."
        if category == "mixed":
            top = sorted(fingerprint.items(), key=lambda item: item[1], reverse=True)[:3]
            return "Mixed patterns detected: " + ", ".join([f"{k}={v:.0%}" for k, v in top if v > 0.0])
        if category == "opaque":
            return "No dominant pattern; manual review recommended."
        return None

    @staticmethod
    def _params_p05(series, **_):
        vals = pd.to_numeric(series, errors="coerce").dropna()
        return f"min={vals.quantile(0.05):.6g}" if not vals.empty else ""

    @staticmethod
    def _params_p95(series, **_):
        vals = pd.to_numeric(series, errors="coerce").dropna()
        return f"max={vals.quantile(0.95):.6g}" if not vals.empty else ""

    @staticmethod
    def _params_char_max(series, char_max_length=0, **_):
        if char_max_length and int(char_max_length) > 0:
            return f"max={int(char_max_length)}"
        stats = ValidationService._compute_string_length_stats(series)
        return f"max={int(max(stats['p95'], 1))}"

    @staticmethod
    def _params_str_p05(series, **_):
        stats = ValidationService._compute_string_length_stats(series)
        return f"min={max(1, int(stats['p05']))}"

    @staticmethod
    def _params_in_list(series, **_):
        vals = [str(v) for v in series.dropna().astype(str).str.strip().unique().tolist() if v != ""]
        vals = sorted(vals)
        return f"allowed={','.join(vals)}" if 0 < len(vals) <= 15 else ""

    @staticmethod
    def _params_gender_codes(series, **_):
        return "allowed=M,F,O,Male,Female,Other,Prefer not to say"

    @staticmethod
    def _params_date_min_bound(series, **_):
        return "min_date=1900-01-01"

    @staticmethod
    def get_column_context(table: str, column: str) -> dict:
        if not ValidationService._is_safe_identifier(table) or not ValidationService._is_safe_identifier(column):
            return {"category": "opaque", "fingerprint": {}, "null_rate": 0.0, "warning": "Unsafe identifier."}
        schema = ValidationService.get_table_schema(table)
        row = schema[schema["COLUMN_NAME"] == column] if not schema.empty else pd.DataFrame()
        if row.empty:
            return {"category": "opaque", "fingerprint": {}, "null_rate": 0.0, "warning": "Schema not found."}
        data_type = str(row.iloc[0]["DATA_TYPE"]).lower()
        null_rate = ValidationService._fetch_null_rate(table, column)
        sample_df = ValidationService._fetch_non_null_sample(table, column, target=150, max_scan=3000)
        sample = sample_df["sample_value"] if not sample_df.empty else pd.Series(dtype="object")
        detectors = {k: v["detector"] for k, v in ValidationService.RULE_SIGNAL_MAP.items() if v.get("detector")}
        context = ValidationService._classify_column(data_type, null_rate, sample, detectors)
        context["warning"] = ValidationService._get_context_warning(context["category"], context["fingerprint"], context["null_rate"])
        return context

    @staticmethod
    def suggest_rules(table: str, column: str, sample_size: int = 200) -> list[dict]:
        if not ValidationService._is_safe_identifier(table) or not ValidationService._is_safe_identifier(column):
            return []

        # PASS 0
        schema = ValidationService.get_table_schema(table)
        if schema.empty:
            return []
        row = schema[schema["COLUMN_NAME"] == column]
        if row.empty:
            return []
        data_type = str(row.iloc[0]["DATA_TYPE"]).lower()
        char_max = int(row.iloc[0]["CHARACTER_MAXIMUM_LENGTH"]) if pd.notna(row.iloc[0]["CHARACTER_MAXIMUM_LENGTH"]) and int(row.iloc[0]["CHARACTER_MAXIMUM_LENGTH"]) > 0 else 0
        null_rate = ValidationService._fetch_null_rate(table, column)
        sample_df = ValidationService._fetch_non_null_sample(table, column, target=min(max(sample_size, 1), 150), max_scan=3000)
        series = sample_df["sample_value"] if not sample_df.empty else pd.Series(dtype="object")
        str_series = series.dropna().astype(str).str.strip()

        detectors = {code: rule["detector"] for code, rule in ValidationService.RULE_SIGNAL_MAP.items() if rule.get("detector")}
        # PASS 1
        context = ValidationService._classify_column(data_type, null_rate, str_series, detectors)
        warning = ValidationService._get_context_warning(context["category"], context["fingerprint"], null_rate)
        suggestions = {}

        def add(code, params, confidence, rationale, source):
            category = ValidationService.RULE_SIGNAL_MAP.get(code, {}).get("category", "integrity")
            ValidationService._upsert_suggestion(suggestions, code, params, confidence, rationale, source, category)

        col_lower = column.lower()
        is_sparse_path = context["category"] in {"sparse", "free_text", "opaque"}

        # PASS 2 type-driven rules
        if not is_sparse_path:
            for code, meta in ValidationService.RULE_SIGNAL_MAP.items():
                dtypes = meta["data_types"]
                if "*" in dtypes or data_type in dtypes:
                    add(code, "", meta["base_conf"], f"Type-aligned with {data_type}.", "statistical")

        # PASS 3 semantic keyword scan
        for code, meta in ValidationService.RULE_SIGNAL_MAP.items():
            if any(k in col_lower for k in meta["keywords"]):
                # Boost confidence for keyword matches to ensure survival of quality filter
                conf = max(meta["base_conf"], 0.85) if any(k == col_lower for k in meta["keywords"]) else max(meta["base_conf"], 0.80)
                add(code, "", conf, f"Column name implies {code}.", "semantic")

        # PASS 4 statistical inference
        num = pd.to_numeric(str_series, errors="coerce").dropna()
        if not num.empty:
            add("min_value", ValidationService._params_p05(str_series), 0.88, "Lower percentile bound inferred.", "statistical")
            add("max_value", ValidationService._params_p95(str_series), 0.88, "Upper percentile bound inferred.", "statistical")
            if (num >= 0).mean() >= 0.95:
                add("positive_only", "", 0.86, "Most values are non-negative.", "statistical")
            if ((num >= 0) & (num <= 100)).mean() >= 0.90:
                add("percentage_range", "", 0.86, "Values concentrated in percentage range.", "statistical")
        if null_rate == 0.0:
            add("NOT_NULL", "", 0.92, "Full-table null rate is 0.", "statistical")
        if data_type in ValidationService.STRING_TYPES:
            sstats = ValidationService._compute_string_length_stats(str_series)
            add("HasLength", f"max={char_max or int(max(sstats['p95'], 1))}", 0.86, "Length cap recommended.", "statistical")
            if any(k in col_lower for k in ("code", "key", "id", "ref")) and sstats["p05"] > 0:
                add("min_length", f"min={int(max(1, sstats['p05']))}", 0.78, "Identifier-like strings have minimum practical length.", "statistical")
            if data_type == "char" and char_max:
                add("exact_length", f"length={char_max}", 0.9, "CHAR column is fixed width.", "statistical")

        # PASS 5 cardinality
        non_null_count = len(str_series)
        unique_values = str_series.unique().tolist() if non_null_count else []
        unique_count = len(unique_values)
        if 0 < unique_count <= 15 and non_null_count > 0:
            add("is_in_list", f"allowed={','.join(map(str, sorted(unique_values)))}", 0.85, "Low cardinality detected.", "cardinality")
        if non_null_count > 0 and (unique_count / non_null_count) >= 0.98 and any(k in col_lower for k in ["id", "key", "code", "ref", "uuid", "guid"]):
            add("is_unique", "", 0.9, "Near-unique identifier pattern.", "cardinality")

        # PASS 6 pattern matching (Regex + Structural)
        for code, meta in ValidationService.RULE_SIGNAL_MAP.items():
            if non_null_count == 0:
                continue
            
            rate = 0.0
            source = "pattern"
            
            if "structural" in meta:
                rate = ValidationService._detect_structural_pattern(str_series, meta["structural"])
                source = "structural"
            elif meta.get("detector"):
                rate = float(str_series.str.match(meta["detector"], na=False).mean())
            else:
                continue
                
            if rate >= 0.70:
                conf = min(0.96, meta["base_conf"] + (0.15 * rate))
                add(code, "", conf, f"{source.capitalize()} matched {rate:.0%} of sampled values.", source)

        # PASS 7 agreement scoring & statistical boosting
        for code in list(suggestions.keys()):
            rule = ValidationService.RULE_SIGNAL_MAP.get(code, {})
            name_implies = any(k in col_lower for k in rule.get("keywords", []))
            
            # Boost based on entropy / profile
            if code == "is_json":
                if context["entropy"] > 3.5 and context["char_profile"]["symbol"] > 0.15:
                    suggestions[code]["confidence"] = min(0.99, suggestions[code]["confidence"] + 0.1)
                    suggestions[code]["rationale"] += " (Consistent with high-symbol entropy profile)"
            
            if code == "masked_value":
                if context["entropy"] > 4.5 and context["unique_ratio"] > 0.9:
                    suggestions[code]["confidence"] = min(0.98, suggestions[code]["confidence"] + 0.15)
                    suggestions[code]["rationale"] += " (Matches high-entropy/unique sensitive pattern)"

            # Semantic Agreement
            if name_implies:
                suggestions[code]["confidence"] = round(min(0.99, suggestions[code]["confidence"] + 0.05), 2)
                suggestions[code]["source"] = "agreement"

        # PASS 8 business injection
        business_by_name = [
            "luhn_check", "iban_checksum", "email_domain_whitelist", "date_not_weekend", "date_not_holiday",
            "non_overlapping_range", "positive_balance", "gender_code", "no_cleartext_password", "masked_value",
        ]
        for code in business_by_name:
            if any(k in col_lower for k in ValidationService.RULE_SIGNAL_MAP[code]["keywords"]):
                params = ValidationService._params_gender_codes(str_series) if code == "gender_code" else ""
                add(code, params, ValidationService.RULE_SIGNAL_MAP[code]["base_conf"], "Keyword-triggered business/security rule.", "business")

        # PASS 9 Cross-Column Heuristics
        other_columns = [c for c in schema["COLUMN_NAME"].tolist() if c.lower() != col_lower]
        for other in other_columns:
            other_lower = other.lower()
            # Temporal bound detection
            if ("start" in col_lower and "end" in other_lower) or ("from" in col_lower and "to" in other_lower):
                if data_type in ValidationService.DATE_TYPES or "date" in col_lower:
                    add("ColumnComparison", f"operator=>,compare_to={other}", 0.82, f"Detected temporal pair with {other}.", "correlation")
            # Foreign Key detection
            if col_lower.endswith("_id") and any(other_lower == col_lower.replace("_id", "") + "_fk" for other in other_columns):
                 add("foreign_key_check", "", 0.78, f"Implied relationship with {other}.", "correlation")

        # PASS 10 sparse/free_text/opaque override path
        if is_sparse_path:
            safe_codes = ["HasLength", "no_sql_injection", "no_html_tags", "trimmed", "no_pii_pattern"]
            if null_rate >= 0.9:
                add("HasLength", f"max={char_max or 4000}", 0.78, "Sparse column safe max length.", "hygiene")
            for code in safe_codes:
                if code in ValidationService.RULE_SIGNAL_MAP:
                    add(code, "", max(0.7, ValidationService.RULE_SIGNAL_MAP[code]["base_conf"]), "Context-based hygiene fallback.", "hygiene")

        # PASS 11 dedupe + sort
        results = [v for v in suggestions.values() if v["confidence"] >= 0.8]
        if warning:
            for item in results:
                item["rationale"] = f"{warning} {item['rationale']}"
        results.sort(key=lambda r: r["confidence"], reverse=True)
        return results

    @staticmethod
    def save_schedule(frequency: str, scheduled_time: str, target_tables: list[str]):
        """Save or update validation schedule."""
        from services.validation_service import execute_sql
        tables_str = ",".join(target_tables) if target_tables else None
        return execute_sql(
            """
            IF EXISTS (SELECT 1 FROM dbo.validation_schedules WHERE frequency = ?)
                UPDATE dbo.validation_schedules 
                SET scheduled_time = ?, target_tables = ?, is_active = 1 
                WHERE frequency = ?
            ELSE
                INSERT INTO dbo.validation_schedules (frequency, scheduled_time, target_tables, is_active)
                VALUES (?, ?, ?, 1)
            """,
            [frequency, scheduled_time, tables_str, frequency, frequency, scheduled_time, tables_str]
        )
