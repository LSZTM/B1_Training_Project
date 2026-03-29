import pandas as pd
import logging
import re
from contextlib import contextmanager
from utils.db import get_connection, close_connection

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, filename="validation.log")


# =========================================================
# DATABASE UTILITIES (DRY CORE)
# =========================================================

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
        logger.error(f"fetch_df failed: {e}")
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
        logger.error(f"fetch_value failed: {e}")
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
        logger.error(f"execute_sql failed: {e}")
        return False


# =========================================================
# VALIDATION SERVICE
# =========================================================

class ValidationService:
    NUMERIC_TYPES = {
        "int", "bigint", "smallint", "tinyint",
        "decimal", "numeric", "float", "real",
        "money", "smallmoney",
    }

    @staticmethod
    def _is_safe_identifier(value):
        return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value or ""))

    @staticmethod
    def _quote_identifier(value):
        return f"[{value}]"

    @staticmethod
    def _upsert_suggestion(bucket, rule_code, rule_params, confidence, rationale):
        existing = bucket.get(rule_code)
        suggestion = {
            "rule_code": rule_code,
            "rule_params": rule_params or "",
            "confidence": round(float(confidence), 2),
            "rationale": rationale,
        }
        if not existing or suggestion["confidence"] > existing["confidence"]:
            bucket[rule_code] = suggestion
        elif existing["rationale"] != rationale:
            existing["rationale"] = f"{existing['rationale']} | {rationale}"

    # =====================================================
    # VALIDATION EXECUTION
    # =====================================================

    @staticmethod
    def run_all_validations():
        """Execute validation stored procedure."""
        try:
            with db_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("EXEC dbo.execute_all_validations")
                conn.commit()

                cursor.execute("""
                    SELECT TOP 1 run_id, total_records_scanned,
                           total_errors, duration_ms, status
                    FROM validation_run_history
                    ORDER BY run_id DESC
                """)
                result = cursor.fetchone()

            if result:
                logger.info(f"Validation run: {result[2]} errors")
                return {
                    "success": True,
                    "run_id": result[0],
                    "records_scanned": result[1],
                    "total_errors": result[2],
                    "duration_ms": result[3],
                    "status": result[4],
                }

            return {"success": True}

        except Exception as e:
            logger.error(f"run_all_validations failed: {e}")
            return {"success": False, "error": str(e)}

    # =====================================================
    # DASHBOARD METRICS
    # =====================================================

    @staticmethod
    def get_metrics():
        """Return dashboard metrics."""
        try:
            rules = fetch_value(
                "SELECT COUNT(*) FROM temp_validation_config WHERE is_active = 1"
            )

            codes = fetch_value("SELECT COUNT(*) FROM error_code_master")
            errors = fetch_value("SELECT COUNT(*) FROM error_log")

            recent = fetch_df("""
                SELECT TOP 1 total_errors, total_records_scanned,
                       DATEDIFF(MINUTE, run_timestamp, GETDATE()) AS minutes_ago
                FROM validation_run_history
                ORDER BY run_id DESC
            """)

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
            logger.error(f"get_metrics failed: {e}")
            return {"rules": 0, "codes": 0, "errors": 0}

    # =====================================================
    # ERROR ANALYTICS
    # =====================================================

    @staticmethod
    def get_recent_errors(limit=10):
        return fetch_df("""
            SELECT TOP (?) table_name, record_identifier,
                   failed_field, error_code, log_time
            FROM error_log
            ORDER BY log_time DESC
        """, [limit])

    @staticmethod
    def get_error_summary_by_table():
        return fetch_df("""
            SELECT table_name,
                   COUNT(*) AS error_count,
                   COUNT(DISTINCT record_identifier) AS affected_records
            FROM error_log
            GROUP BY table_name
            ORDER BY error_count DESC
        """)

    # =====================================================
    # ERROR EXPLORER
    # =====================================================

    @staticmethod
    def get_tables():
        df = fetch_df("""
            SELECT DISTINCT table_name
            FROM error_log
            ORDER BY table_name
        """)
        return df["table_name"].tolist() if not df.empty else []

    @staticmethod
    def get_columns(table_name=None):
        if table_name:
            df = fetch_df("""
                SELECT DISTINCT failed_field
                FROM error_log
                WHERE table_name = ?
                ORDER BY failed_field
            """, [table_name])
        else:
            df = fetch_df("""
                SELECT DISTINCT failed_field
                FROM error_log
                ORDER BY failed_field
            """)
        return df["failed_field"].tolist() if not df.empty else []

    @staticmethod
    def get_error_codes():
        df = fetch_df("""
            SELECT DISTINCT error_code
            FROM error_log
            ORDER BY error_code
        """)
        return df["error_code"].tolist() if not df.empty else []

    @staticmethod
    def get_filtered_errors(table=None, column=None, error_code=None, limit=500):
        query = """
            SELECT TOP (?) table_name, record_identifier,
                   failed_field, error_code, log_time
            FROM error_log
            WHERE 1=1
        """
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

    # =====================================================
    # RUN HISTORY
    # =====================================================

    @staticmethod
    def get_run_history(limit=50):
        return fetch_df("""
            SELECT TOP (?)
                run_id,
                run_timestamp,
                total_records_scanned,
                total_errors,
                duration_ms,
                status
            FROM validation_run_history
            ORDER BY run_id DESC
        """, [limit])

    @staticmethod
    def get_run_details(run_id):
        summary = fetch_df("""
            SELECT run_id, run_timestamp, total_records_scanned,
                   total_errors, duration_ms, status
            FROM validation_run_history
            WHERE run_id = ?
        """, [run_id])

        errors = fetch_df("""
            SELECT table_name, COUNT(*) AS error_count
            FROM error_log
            WHERE run_id = ?
            GROUP BY table_name
            ORDER BY error_count DESC
        """, [run_id])

        return {
            "summary": summary.iloc[0].to_dict() if not summary.empty else {},
            "errors_by_table": errors.to_dict(orient="records"),
        }

    # =====================================================
    # RULE MANAGEMENT
    # =====================================================

    @staticmethod
    def get_validation_rules():
        return fetch_df("""
            SELECT *
            FROM dbo.temp_validation_config
            WHERE is_active = 1
            ORDER BY table_name, column_name
        """)

    @staticmethod
    def delete_validation_rule(table, column, rule_code):
        return execute_sql("""
            DELETE FROM dbo.temp_validation_config
            WHERE table_name = ? AND column_name = ? AND rule_code = ?
        """, [table, column, rule_code])

    @staticmethod
    def add_validation_rule(table, column, rule_code, rule_params,
                            allow_null, is_active, error_code,
                            comparison_column=None):
        try:
            with db_conn() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    IF NOT EXISTS (SELECT 1 FROM error_code_master WHERE error_code = ?)
                    INSERT INTO error_code_master
                    (error_code, rule_name, description, severity)
                    VALUES (?, ?, ?, 'MEDIUM')
                """,
                error_code,
                error_code,
                f"{rule_code} validation failed on {table}.{column}",
                )

                cursor.execute("""
                    INSERT INTO dbo.temp_validation_config
                    (table_name, column_name, rule_code, rule_params,
                     allow_null, is_active, error_code, comparison_column)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                table, column, rule_code, rule_params,
                int(allow_null), int(is_active), error_code,
                comparison_column,
                )

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"add_validation_rule failed: {e}")
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
                        cursor.execute("""
                            INSERT INTO dbo.temp_validation_config
                            (table_name, column_name, rule_code,
                             rule_params, allow_null, is_active, error_code)
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
            logger.error(f"bulk_import_rules failed: {e}")

        return success

    # =====================================================
    # METADATA
    # =====================================================

    @staticmethod
    def get_db_tables():
        df = fetch_df("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE='BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        return df["TABLE_NAME"].tolist() if not df.empty else []

    @staticmethod
    def get_table_columns(table):
        df = fetch_df("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            ORDER BY COLUMN_NAME
        """, [table])
        return df["COLUMN_NAME"].tolist() if not df.empty else []
    @staticmethod
    def get_table_schema(table):
        """Return a DataFrame with column name, data type, nullability, etc. for the given table."""
        query = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """
        return fetch_df(query, [table])

    @staticmethod
    def suggest_rules(table, column, sample_size=200):
        """Suggest validation rules for a table column using semantic/statistical/profile passes."""
        if not ValidationService._is_safe_identifier(table) or not ValidationService._is_safe_identifier(column):
            return []

        schema = ValidationService.get_table_schema(table)
        if schema.empty:
            return []

        schema_row = schema[schema["COLUMN_NAME"] == column]
        if schema_row.empty:
            return []

        data_type = str(schema_row.iloc[0]["DATA_TYPE"]).lower()
        suggestions = {}

        # Pass 1: semantic name matching
        col_name = column.lower()
        semantic_rules = [
            (("dob", "birth", "date", "_at", "time"), "IsDate", "format=YYYY-MM-DD", 0.95, "Column name indicates a date/time field."),
            (("email", "mail"), "IsEmail", "", 0.95, "Column name indicates an email field."),
            (("phone", "mobile", "tel"), "is_phone", "format=E164", 0.92, "Column name indicates a phone field."),
            (("ssn", "tax", "national_id"), "is_ssn", "", 0.92, "Column name indicates a national identifier field."),
            (("url", "website", "link"), "is_url", "", 0.9, "Column name indicates a URL field."),
        ]

        for keywords, code, params, confidence, rationale in semantic_rules:
            if any(keyword in col_name for keyword in keywords):
                ValidationService._upsert_suggestion(
                    suggestions, code, params, confidence, f"Semantic pass: {rationale}"
                )

        query = f"""
            SELECT TOP ({int(sample_size)}) {ValidationService._quote_identifier(column)} AS sample_value
            FROM {ValidationService._quote_identifier(table)}
        """
        sample_df = fetch_df(query)
        if sample_df.empty:
            return list(suggestions.values())

        raw_series = sample_df["sample_value"]
        non_null = raw_series.dropna()
        non_null_count = len(non_null)
        total_count = len(raw_series)

        if non_null_count == 0:
            return list(suggestions.values())

        # Pass 2: statistical inference
        if data_type in ValidationService.NUMERIC_TYPES:
            numeric_series = pd.to_numeric(non_null, errors="coerce").dropna()
            if not numeric_series.empty:
                q05 = float(numeric_series.quantile(0.05))
                q95 = float(numeric_series.quantile(0.95))
                ValidationService._upsert_suggestion(
                    suggestions,
                    "is_digit",
                    "",
                    0.87,
                    "Statistical pass: Numeric SQL data type detected.",
                )
                ValidationService._upsert_suggestion(
                    suggestions,
                    "min_value",
                    f"value={q05:.4f}",
                    0.83,
                    "Statistical pass: 5th percentile used as robust minimum.",
                )
                ValidationService._upsert_suggestion(
                    suggestions,
                    "max_value",
                    f"value={q95:.4f}",
                    0.83,
                    "Statistical pass: 95th percentile used as robust maximum.",
                )

        null_count = int(total_count - non_null_count)
        if null_count == 0:
            ValidationService._upsert_suggestion(
                suggestions,
                "NOT_NULL",
                "",
                0.8,
                "Statistical pass: No NULL values found in sampled rows.",
            )

        # Pass 3: cardinality detection
        value_strings = non_null.astype(str).str.strip()
        unique_values = sorted(value_strings.unique().tolist())
        unique_count = len(unique_values)
        distinct_ratio = unique_count / max(non_null_count, 1)

        if distinct_ratio <= 0.10 and unique_count < 15:
            allowed_values = ",".join(unique_values)
            ValidationService._upsert_suggestion(
                suggestions,
                "is_in_list",
                f"values={allowed_values}",
                0.84,
                f"Cardinality pass: {unique_count} distinct values across {non_null_count} sampled rows.",
            )

        # Pass 4: pattern matching (80% threshold)
        pattern_checks = [
            ("IsEmail", r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", "", "Pattern pass: Email shape match in sampled rows."),
            ("is_phone", r"^\+[1-9]\d{7,14}$", "format=E164", "Pattern pass: E.164 phone format detected."),
            ("is_ssn", r"^\d{3}-\d{2}-\d{4}$", "", "Pattern pass: SSN format detected."),
            ("is_url", r"^https?://[^\s/$.?#].[^\s]*$", "", "Pattern pass: URL structure detected."),
            ("IsDate", r"^\d{4}-\d{2}-\d{2}$", "format=YYYY-MM-DD", "Pattern pass: ISO date format detected."),
        ]
        for code, regex, params, rationale in pattern_checks:
            matches = value_strings.str.match(regex, na=False).sum()
            ratio = matches / max(non_null_count, 1)
            if ratio >= 0.80:
                ValidationService._upsert_suggestion(
                    suggestions,
                    code,
                    params,
                    0.7 + (0.2 * ratio),
                    f"{rationale} Match rate: {ratio:.0%}.",
                )

        return sorted(
            suggestions.values(),
            key=lambda item: item["confidence"],
            reverse=True,
        )
