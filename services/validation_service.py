import base64
import json
import logging
import re
from contextlib import contextmanager

import pandas as pd

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
        return False


class ValidationService:
    NOT_IMPLEMENTED_RULES = {
        "foreign_key_check",
        "non_overlapping_range",
        "date_not_holiday",
    }
    NUMERIC_TYPES = {
        "int", "bigint", "smallint", "tinyint", "decimal", "numeric", "float", "real", "money", "smallmoney"
    }
    STRING_TYPES = {"varchar", "nvarchar", "char", "nchar", "text", "ntext"}
    DATE_TYPES = {"date", "datetime", "datetime2", "smalldatetime", "timestamp", "time"}

    RULE_SIGNAL_MAP: dict[str, dict] = {
        # TYPE
        "NOT_NULL": {"keywords": ["required", "mandatory", "id", "key"], "data_types": ["*"], "detector": None, "params_fn": None, "base_conf": 0.82, "category": "type", "description": "Column must not be null."},
        "is_digit": {"keywords": ["id", "qty", "count"], "data_types": ["int", "bigint", "smallint", "tinyint"], "detector": None, "params_fn": None, "base_conf": 0.85, "category": "type", "description": "Whole number type validation."},
        "is_decimal": {"keywords": ["amount", "price", "cost"], "data_types": ["decimal", "numeric", "float", "real", "money"], "detector": None, "params_fn": None, "base_conf": 0.84, "category": "type", "description": "Decimal numeric validation."},
        "is_boolean": {"keywords": ["is_", "flag", "active", "enabled"], "data_types": ["bit", "bool"], "detector": r"^(0|1|true|false|yes|no|t|f)$", "params_fn": None, "base_conf": 0.82, "category": "type", "description": "Boolean domain validation."},
        "is_integer_string": {"keywords": ["id", "code", "number"], "data_types": ["varchar", "char"], "detector": r"^-?\d+$", "params_fn": None, "base_conf": 0.76, "category": "type", "description": "String that should contain integer text."},
        # FORMAT
        "IsEmail": {"keywords": ["email", "mail"], "data_types": ["varchar", "nvarchar"], "detector": r"^(?=.{1,254}$)(?=.{1,64}@)[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$", "params_fn": None, "base_conf": 0.86, "category": "format", "description": "Email address format."},
        "is_phone_e164": {"keywords": ["phone", "mobile", "tel"], "data_types": ["varchar", "nvarchar"], "detector": r"^\+[1-9]\d{7,14}$", "params_fn": None, "base_conf": 0.82, "category": "format", "description": "E.164 phone format."},
        "is_phone_us": {"keywords": ["phone", "mobile", "tel"], "data_types": ["varchar", "nvarchar"], "detector": r"^(\(\d{3}\))?[\s-]?\d{3}[\s-]?\d{4}$", "params_fn": None, "base_conf": 0.8, "category": "format", "description": "US phone format."},
        "IsDate": {"keywords": ["date", "dob", "birth"], "data_types": ["date", "datetime", "varchar"], "detector": r"^\d{4}-\d{2}-\d{2}$", "params_fn": None, "base_conf": 0.84, "category": "format", "description": "Date string format."},
        "is_datetime": {"keywords": ["time", "timestamp", "created", "updated"], "data_types": ["datetime", "datetime2", "varchar"], "detector": r"^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}(:\d{2})?$", "params_fn": None, "base_conf": 0.83, "category": "format", "description": "Datetime format."},
        "is_time": {"keywords": ["time", "hour"], "data_types": ["time", "varchar"], "detector": r"^\d{2}:\d{2}(:\d{2})?$", "params_fn": None, "base_conf": 0.8, "category": "format", "description": "Time format."},
        "is_uuid": {"keywords": ["uuid", "guid", "id"], "data_types": ["varchar", "char"], "detector": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", "params_fn": None, "base_conf": 0.84, "category": "format", "description": "UUID format."},
        "is_ssn": {"keywords": ["ssn", "social"], "data_types": ["varchar", "char"], "detector": r"^\d{3}-\d{2}-\d{4}$", "params_fn": None, "base_conf": 0.8, "category": "format", "description": "US SSN format."},
        "is_postal_code_us": {"keywords": ["zip", "postal"], "data_types": ["varchar", "char"], "detector": r"^\d{5}(-\d{4})?$", "params_fn": None, "base_conf": 0.78, "category": "format", "description": "US postal code."},
        "is_postal_code_uk": {"keywords": ["postcode", "postal"], "data_types": ["varchar", "char"], "detector": r"^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$", "params_fn": None, "base_conf": 0.78, "category": "format", "description": "UK postal code."},
        "is_ip_v4": {"keywords": ["ip", "ipv4"], "data_types": ["varchar", "nvarchar"], "detector": r"^(\d{1,3}\.){3}\d{1,3}$", "params_fn": None, "base_conf": 0.77, "category": "format", "description": "IPv4 format."},
        "is_ip_v6": {"keywords": ["ip", "ipv6"], "data_types": ["varchar", "nvarchar"], "detector": r"^([0-9a-f]{1,4}:){7}[0-9a-f]{1,4}$", "params_fn": None, "base_conf": 0.77, "category": "format", "description": "IPv6 format."},
        "is_url": {"keywords": ["url", "link", "website"], "data_types": ["varchar", "nvarchar"], "detector": r"^https?://[^\s/$.?#].[^\s]*$", "params_fn": None, "base_conf": 0.8, "category": "format", "description": "HTTP/HTTPS URL."},
        "is_credit_card": {"keywords": ["card", "credit", "debit", "pan"], "data_types": ["varchar", "char"], "detector": r"^\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}$", "params_fn": None, "base_conf": 0.76, "category": "format", "description": "Credit card number format."},
        "is_iban": {"keywords": ["iban", "bank", "account"], "data_types": ["varchar", "char"], "detector": r"^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$", "params_fn": None, "base_conf": 0.77, "category": "format", "description": "IBAN format."},
        "is_currency_code": {"keywords": ["currency", "ccy"], "data_types": ["varchar", "char"], "detector": r"^[A-Z]{3}$", "params_fn": None, "base_conf": 0.78, "category": "format", "description": "ISO currency code."},
        "is_country_code": {"keywords": ["country", "nation"], "data_types": ["varchar", "char"], "detector": r"^[A-Z]{2}$", "params_fn": None, "base_conf": 0.78, "category": "format", "description": "ISO country code."},
        "is_json": {"keywords": ["json", "payload", "metadata"], "data_types": ["varchar", "nvarchar", "text"], "detector": None, "params_fn": None, "base_conf": 0.78, "category": "format", "description": "Valid JSON payload."},
        "is_base64": {"keywords": ["base64", "blob", "encoded"], "data_types": ["varchar", "nvarchar"], "detector": r"^[A-Za-z0-9+/]+={0,2}$", "params_fn": None, "base_conf": 0.75, "category": "format", "description": "Base64 text."},
        "is_hex_color": {"keywords": ["color", "colour", "hex"], "data_types": ["varchar", "char"], "detector": r"^#[0-9A-Fa-f]{6}$", "params_fn": None, "base_conf": 0.76, "category": "format", "description": "Hex color code."},
        "is_latitude": {"keywords": ["lat", "latitude"], "data_types": ["decimal", "float", "varchar"], "detector": None, "params_fn": None, "base_conf": 0.8, "category": "format", "description": "Latitude range check."},
        "is_longitude": {"keywords": ["lon", "lng", "longitude"], "data_types": ["decimal", "float", "varchar"], "detector": None, "params_fn": None, "base_conf": 0.8, "category": "format", "description": "Longitude range check."},
        # RANGE
        "min_value": {"keywords": ["min", "lower"], "data_types": ["int", "bigint", "smallint", "tinyint", "decimal", "numeric", "float", "real", "money"], "detector": None, "params_fn": "_params_p05", "base_conf": 0.82, "category": "range", "description": "Lower bound from sample p05."},
        "max_value": {"keywords": ["max", "upper"], "data_types": ["int", "bigint", "smallint", "tinyint", "decimal", "numeric", "float", "real", "money"], "detector": None, "params_fn": "_params_p95", "base_conf": 0.82, "category": "range", "description": "Upper bound from sample p95."},
        "date_not_in_future": {"keywords": ["date", "created", "posted"], "data_types": ["date", "datetime", "datetime2"], "detector": None, "params_fn": None, "base_conf": 0.8, "category": "range", "description": "Date cannot be in future."},
        "date_not_before_epoch": {"keywords": ["date", "time", "epoch"], "data_types": ["date", "datetime", "datetime2"], "detector": None, "params_fn": None, "base_conf": 0.78, "category": "range", "description": "Date not before 1970-01-01."},
        "date_min_bound": {"keywords": ["birth", "dob"], "data_types": ["date", "datetime", "datetime2"], "detector": None, "params_fn": "_params_date_min_bound", "base_conf": 0.86, "category": "range", "description": "Date min bound for birth dates."},
        "positive_only": {"keywords": ["price", "amount", "salary", "qty", "quantity", "age"], "data_types": ["int", "bigint", "smallint", "tinyint", "decimal", "numeric", "float", "real", "money"], "detector": None, "params_fn": None, "base_conf": 0.84, "category": "range", "description": "Values should be non-negative."},
        "percentage_range": {"keywords": ["rate", "pct", "percent", "ratio"], "data_types": ["decimal", "numeric", "float", "real"], "detector": None, "params_fn": None, "base_conf": 0.84, "category": "range", "description": "Percentage range 0-100."},
        "age_range": {"keywords": ["age"], "data_types": ["int"], "detector": None, "params_fn": None, "base_conf": 0.87, "category": "range", "description": "Age between 0 and 150."},
        "year_range": {"keywords": ["year", "yr"], "data_types": ["int", "smallint"], "detector": None, "params_fn": None, "base_conf": 0.86, "category": "range", "description": "Year between 1900 and 2100."},
        # LENGTH
        "HasLength": {"keywords": ["name", "desc", "text", "code"], "data_types": ["varchar", "nvarchar", "char", "text"], "detector": None, "params_fn": "_params_char_max", "base_conf": 0.88, "category": "integrity", "description": "Max length aligns with schema."},
        "min_length": {"keywords": ["code", "key", "id", "ref"], "data_types": ["varchar", "nvarchar"], "detector": None, "params_fn": "_params_str_p05", "base_conf": 0.76, "category": "integrity", "description": "Minimum practical string length."},
        "exact_length": {"keywords": ["code", "id", "ssn"], "data_types": ["char"], "detector": None, "params_fn": "_params_char_max", "base_conf": 0.88, "category": "integrity", "description": "Fixed width CHAR length."},
        "no_whitespace_only": {"keywords": ["name", "code", "desc"], "data_types": ["varchar", "nvarchar", "text"], "detector": None, "params_fn": None, "base_conf": 0.74, "category": "hygiene", "description": "Reject whitespace-only strings."},
        "no_leading_whitespace": {"keywords": ["name", "code", "desc"], "data_types": ["varchar", "nvarchar", "text"], "detector": None, "params_fn": None, "base_conf": 0.74, "category": "hygiene", "description": "Reject leading whitespace."},
        "no_trailing_whitespace": {"keywords": ["name", "code", "desc"], "data_types": ["varchar", "nvarchar", "text"], "detector": None, "params_fn": None, "base_conf": 0.74, "category": "hygiene", "description": "Reject trailing whitespace."},
        "no_internal_newline": {"keywords": ["code", "ref", "id"], "data_types": ["varchar", "nvarchar"], "detector": None, "params_fn": None, "base_conf": 0.7, "category": "hygiene", "description": "Reject newline characters."},
        # INTEGRITY
        "is_in_list": {"keywords": ["status", "type", "category"], "data_types": ["*"], "detector": None, "params_fn": "_params_in_list", "base_conf": 0.84, "category": "integrity", "description": "Allowed value list."},
        "is_unique": {"keywords": ["id", "key", "code", "ref", "uuid", "guid"], "data_types": ["*"], "detector": None, "params_fn": None, "base_conf": 0.83, "category": "integrity", "description": "Values should be unique."},
        "ColumnComparison": {"keywords": ["start", "end", "from", "to", "min", "max", "open", "close"], "data_types": ["*"], "detector": None, "params_fn": None, "base_conf": 0.68, "category": "integrity", "description": "Compare with another column."},
        "not_equal_to": {"keywords": ["not", "exclude", "blocked"], "data_types": ["*"], "detector": None, "params_fn": None, "base_conf": 0.65, "category": "integrity", "description": "Not equal forbidden value."},
        "foreign_key_check": {"keywords": ["_id", "_fk", "ref"], "data_types": ["int", "varchar"], "detector": None, "params_fn": None, "base_conf": 0.72, "category": "integrity", "description": "Foreign key existence check."},
        # HYGIENE
        "no_sql_injection": {"keywords": ["comment", "note", "text"], "data_types": ["varchar", "nvarchar", "text"], "detector": None, "params_fn": None, "base_conf": 0.76, "category": "hygiene", "description": "Block SQL injection patterns."},
        "no_html_tags": {"keywords": ["comment", "note", "text"], "data_types": ["varchar", "nvarchar", "text"], "detector": None, "params_fn": None, "base_conf": 0.75, "category": "hygiene", "description": "Block HTML tags."},
        "no_special_chars": {"keywords": ["name", "code", "ref"], "data_types": ["varchar", "nvarchar"], "detector": None, "params_fn": None, "base_conf": 0.73, "category": "hygiene", "description": "Allow alphanumerics and separators only."},
        "encoding_check": {"keywords": ["text", "desc", "comment"], "data_types": ["varchar", "nvarchar", "text"], "detector": None, "params_fn": None, "base_conf": 0.7, "category": "hygiene", "description": "Detect encoding anomalies."},
        "case_consistency": {"keywords": ["status", "type", "category", "code"], "data_types": ["varchar", "char"], "detector": None, "params_fn": None, "base_conf": 0.72, "category": "hygiene", "description": "Consistent letter case."},
        "no_emoji": {"keywords": ["code", "id", "ref", "key"], "data_types": ["varchar", "nvarchar"], "detector": None, "params_fn": None, "base_conf": 0.72, "category": "hygiene", "description": "Disallow emoji characters."},
        "trimmed": {"keywords": ["name", "code", "ref", "text"], "data_types": ["varchar", "nvarchar", "text"], "detector": None, "params_fn": None, "base_conf": 0.74, "category": "hygiene", "description": "Composite trim rule."},
        # BUSINESS
        "luhn_check": {"keywords": ["card", "credit", "debit", "pan"], "data_types": ["varchar", "char"], "detector": None, "params_fn": None, "base_conf": 0.82, "category": "business", "description": "Luhn checksum."},
        "iban_checksum": {"keywords": ["iban", "bank", "account"], "data_types": ["varchar", "char"], "detector": None, "params_fn": None, "base_conf": 0.82, "category": "business", "description": "IBAN mod-97 checksum."},
        "email_domain_whitelist": {"keywords": ["email", "mail"], "data_types": ["varchar", "nvarchar"], "detector": None, "params_fn": None, "base_conf": 0.68, "category": "business", "description": "Email domain whitelist."},
        "date_not_weekend": {"keywords": ["business", "trading", "working"], "data_types": ["date", "datetime", "datetime2"], "detector": None, "params_fn": None, "base_conf": 0.72, "category": "business", "description": "Date must not be weekend."},
        "date_not_holiday": {"keywords": ["business", "trading", "working"], "data_types": ["date", "datetime", "datetime2"], "detector": None, "params_fn": None, "base_conf": 0.68, "category": "business", "description": "Date must not be holiday."},
        "non_overlapping_range": {"keywords": ["start", "end"], "data_types": ["date", "datetime", "datetime2"], "detector": None, "params_fn": None, "base_conf": 0.66, "category": "business", "description": "Ranges should not overlap."},
        "positive_balance": {"keywords": ["balance", "credit", "debit"], "data_types": ["decimal", "money"], "detector": None, "params_fn": None, "base_conf": 0.8, "category": "business", "description": "Balance should be non-negative."},
        "gender_code": {"keywords": ["gender", "sex"], "data_types": ["varchar", "char"], "detector": None, "params_fn": "_params_gender_codes", "base_conf": 0.86, "category": "business", "description": "Gender code domain."},
        # SECURITY
        "no_pii_pattern": {"keywords": ["note", "comment", "text"], "data_types": ["varchar", "nvarchar", "text"], "detector": None, "params_fn": None, "base_conf": 0.8, "category": "security", "description": "Block PII patterns in free text."},
        "masked_value": {"keywords": ["password", "secret", "token", "key", "hash"], "data_types": ["varchar", "char"], "detector": None, "params_fn": None, "base_conf": 0.74, "category": "security", "description": "Value should appear masked."},
        "no_cleartext_password": {"keywords": ["password", "pwd", "passwd", "secret"], "data_types": ["varchar", "nvarchar"], "detector": None, "params_fn": None, "base_conf": 0.88, "category": "security", "description": "Block cleartext password-like values."},
    }

    @staticmethod
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
    def run_all_validations():
        try:
            with db_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("EXEC dbo.execute_all_validations")
                conn.commit()
                cursor.execute(
                    """
                    SELECT TOP 1 run_id, total_records_scanned, total_errors, duration_ms, status
                    FROM validation_run_history
                    ORDER BY run_id DESC
                    """
                )
                row = cursor.fetchone()
            if not row:
                return {"success": True}
            return {"success": True, "run_id": row[0], "records_scanned": row[1], "total_errors": row[2], "duration_ms": row[3], "status": row[4]}
        except Exception as e:
            logger.error("run_all_validations failed: %s", e)
            return {"success": False, "error": str(e)}

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
        df = fetch_df("SELECT DISTINCT error_code FROM error_log ORDER BY error_code")
        return df["error_code"].tolist() if not df.empty else []

    @staticmethod
    def get_filtered_errors(table=None, column=None, error_code=None, limit=500):
        query = "SELECT TOP (?) table_name, record_identifier, failed_field, error_code, log_time FROM error_log WHERE 1=1"
        params = [limit]
        if table:
            query += " AND table_name = ?"
            params.append(table)
        if column:
            query += " AND failed_field = ?"
            params.append(column)
        if error_code:
            query += " AND error_code = ?"
            params.append(error_code)
        query += " ORDER BY log_time DESC"
        return fetch_df(query, params)

    @staticmethod
    def clear_error_log():
        return execute_sql("TRUNCATE TABLE error_log")

    @staticmethod
    def get_rule_implementation_map():
        status_map = {code: True for code in ValidationService.RULE_SIGNAL_MAP.keys()}
        for code in ValidationService.NOT_IMPLEMENTED_RULES:
            status_map[code] = False

        df = fetch_df("SELECT rule_code, is_implemented FROM dbo.rule_implementation_status")
        if not df.empty:
            for _, row in df.iterrows():
                status_map[str(row["rule_code"])] = bool(row["is_implemented"])
        return status_map

    @staticmethod
    def get_active_rules():
        return fetch_df("""SELECT id, table_name, column_name, rule_code, rule_params, allow_null, is_active, error_code, comparison_column FROM temp_validation_config ORDER BY table_name, column_name""")

    @staticmethod
    def get_validation_rules():
        return ValidationService.get_active_rules()

    @staticmethod
    def toggle_rule(rule_id, is_active):
        return execute_sql("UPDATE temp_validation_config SET is_active = ? WHERE id = ?", [int(bool(is_active)), rule_id])

    @staticmethod
    def delete_rule(rule_id):
        return execute_sql("DELETE FROM temp_validation_config WHERE id = ?", [rule_id])

    @staticmethod
    def add_validation_rule(rule: Rule):
        if not isinstance(rule, Rule):
            raise TypeError("add_validation_rule expects a Rule object.")

        if not rule.is_implemented:
            logger.warning("Rejected add_validation_rule for not implemented rule: %s", rule.rule_code)
            return False
        try:
            with db_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO dbo.temp_validation_config
                    (table_name, column_name, rule_code, rule_params, allow_null, is_active, error_code, comparison_column)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    *rule.to_insert_params(),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error("add_validation_rule failed: %s", e)
            return False

    @staticmethod
    def bulk_import_rules(df):
        success = 0
        try:
            with db_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("TRUNCATE TABLE dbo.temp_validation_config")
                for _, row in df.iterrows():
                    try:
                        cursor.execute(
                            """
                            INSERT INTO dbo.temp_validation_config
                            (table_name, column_name, rule_code, rule_params, allow_null, is_active, error_code)
                            VALUES (?, ?, ?, ?, ?, 1, ?)
                            """,
                            row["table_name"],
                            row["column_name"],
                            row["rule_code"],
                            row.get("rule_params"),
                            int(row.get("allow_null", 0)),
                            row.get("error_code", "E000"),
                        )
                        success += 1
                    except Exception:
                        continue
                conn.commit()
        except Exception as e:
            logger.error("bulk_import_rules failed: %s", e)
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
    def _attempt_json_parse(series: pd.Series) -> float:
        if series.empty:
            return 0.0
        total = 0
        ok = 0
        for value in series.dropna().astype(str):
            total += 1
            try:
                json.loads(value)
                ok += 1
            except Exception:
                pass
        return round(ok / max(total, 1), 4)

    @staticmethod
    def _classify_column(data_type: str, null_rate: float, non_null_sample: pd.Series, detectors: dict[str, str]) -> dict:
        values = non_null_sample.dropna().astype(str).str.strip()
        fingerprint = {}
        for key, pattern in detectors.items():
            try:
                fingerprint[key] = round(float(values.str.match(pattern, na=False).mean()) if len(values) else 0.0, 4)
            except re.error:
                fingerprint[key] = 0.0
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
                add(code, "", max(meta["base_conf"], 0.78), f"Column name implies {code}.", "semantic")

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

        # PASS 6 pattern matching
        for code, meta in ValidationService.RULE_SIGNAL_MAP.items():
            if meta.get("detector") is None and code != "is_json":
                continue
            if non_null_count == 0:
                continue
            if code == "is_json":
                rate = ValidationService._attempt_json_parse(str_series)
            else:
                rate = float(str_series.str.match(meta["detector"], na=False).mean())
            if rate >= 0.80:
                conf = min(0.95, 0.70 + (0.20 * rate))
                add(code, "", conf, f"Pattern matched {rate:.0%} of sampled values.", "pattern")

        # PASS 7 agreement scoring
        for code in list(suggestions.keys()):
            rule = ValidationService.RULE_SIGNAL_MAP.get(code, {})
            name_implies = any(k in col_lower for k in rule.get("keywords", []))
            detector = rule.get("detector")
            data_confirms = False
            if detector and non_null_count > 0:
                data_confirms = float(str_series.str.match(detector, na=False).mean()) >= 0.80
            elif code in {"min_value", "max_value", "positive_only", "percentage_range", "HasLength"}:
                data_confirms = True
            if name_implies and data_confirms:
                suggestions[code]["confidence"] = round(min(0.99, suggestions[code]["confidence"] + 0.05), 2)
                suggestions[code]["source"] = "agreement"
            elif name_implies and not data_confirms and detector:
                suggestions.pop(code, None)

        # PASS 8 business injection
        business_by_name = [
            "luhn_check", "iban_checksum", "email_domain_whitelist", "date_not_weekend", "date_not_holiday",
            "non_overlapping_range", "positive_balance", "gender_code", "no_cleartext_password", "masked_value",
        ]
        for code in business_by_name:
            if any(k in col_lower for k in ValidationService.RULE_SIGNAL_MAP[code]["keywords"]):
                params = ValidationService._params_gender_codes(str_series) if code == "gender_code" else ""
                add(code, params, ValidationService.RULE_SIGNAL_MAP[code]["base_conf"], "Keyword-triggered business/security rule.", "business")

        # sparse/free_text/opaque override path
        if is_sparse_path:
            safe_codes = ["HasLength", "no_sql_injection", "no_html_tags", "encoding_check", "trimmed", "no_pii_pattern"]
            if null_rate >= 0.9:
                add("HasLength", f"max={char_max or 4000}", 0.78, "Sparse column safe max length.", "hygiene")
            for code in safe_codes:
                if code in ValidationService.RULE_SIGNAL_MAP:
                    add(code, "", max(0.7, ValidationService.RULE_SIGNAL_MAP[code]["base_conf"]), "Context-based hygiene fallback.", "hygiene")

        # PASS 9 dedupe + sort
        results = [v for v in suggestions.values() if v["confidence"] > 0]
        if warning:
            for item in results:
                item["rationale"] = f"{warning} {item['rationale']}"
        results.sort(key=lambda r: r["confidence"], reverse=True)
        return results
