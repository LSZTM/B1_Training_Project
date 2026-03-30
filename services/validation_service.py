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
    PATTERN_DETECTORS = {
        "email": r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
        "phone": r"^\+?[1-9]\d{7,14}$",
        "ssn": r"^\d{3}-\d{2}-\d{4}$",
        "iso_date": r"^\d{4}-\d{2}-\d{2}$",
        "url": r"^https?://[^\s/$.?#].[^\s]*$",
        "integer": r"^\-?\d+$",
        "decimal": r"^\-?\d+\.\d+$",
        "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    }
    HYGIENE_RULES = [
        ("HasLength", "max={char_limit}", 0.88, "Enforce DB column character limit."),
        ("no_sql_injection", "block=<script>,DROP,--", 0.82, "Free-text fields are injection vectors."),
        ("no_leading_whitespace", "", 0.78, "Trim artifacts common in free-text entry."),
        ("allow_null", "", 0.92, "Free-text fields are almost always optional."),
        ("encoding_check", "expected=UTF-8", 0.70, "Legacy data often has encoding corruption."),
    ]
    SPARSE_RULES = [
        ("allow_null", "", 0.99, "Column is {null_pct}% NULL — enforcing NOT_NULL would fail almost every row."),
        ("HasLength", "max={char_limit}", 0.75, "Length cap is safe regardless of content sparsity."),
    ]

    @staticmethod
    def _is_safe_identifier(value):
        return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value or ""))

    @staticmethod
    def _quote_identifier(value):
        return f"[{value}]"

    @staticmethod
    def _upsert_suggestion(bucket, rule_code, rule_params, confidence, rationale, source):
        existing = bucket.get(rule_code)
        suggestion = {
            "rule_code": rule_code,
            "rule_params": rule_params or "",
            "confidence": round(float(confidence), 2),
            "rationale": rationale,
            "source": source,
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
    def _fetch_non_null_sample(table: str, column: str, target: int = 100, max_scan: int = 2000) -> pd.DataFrame:
        """
        Pull rows until `target` non-null values are collected, scanning at most `max_scan` rows.
        Returns DataFrame with `sample_value` alias.
        """
        try:
            query = f"""
                SELECT TOP ({int(min(max_scan, max(target, 1)))})
                    {ValidationService._quote_identifier(column)} AS sample_value
                FROM {ValidationService._quote_identifier(table)}
                WHERE {ValidationService._quote_identifier(column)} IS NOT NULL
            """
            sample_df = fetch_df(query)
            if sample_df.empty:
                return pd.DataFrame(columns=["sample_value"])
            return sample_df.head(target)
        except Exception as e:
            logger.error(f"_fetch_non_null_sample failed: {e}")
            return pd.DataFrame(columns=["sample_value"])

    @staticmethod
    def _fetch_null_rate(table: str, column: str) -> float:
        """Compute full-table null-rate for a given column."""
        try:
            query = f"""
                SELECT
                    CAST(SUM(CASE WHEN {ValidationService._quote_identifier(column)} IS NULL THEN 1 ELSE 0 END) AS FLOAT)
                    / NULLIF(COUNT(*), 0)
                FROM {ValidationService._quote_identifier(table)}
            """
            result = fetch_value(query, default=0.0)
            return round(float(result or 0.0), 4)
        except Exception as e:
            logger.error(f"_fetch_null_rate failed: {e}")
            return 0.0

    @staticmethod
    def _classify_column(data_type: str, null_rate: float, non_null_sample: pd.Series, detectors: dict[str, str]) -> dict:
        """Classify column shape from null-rate and pattern fingerprint."""
        values = non_null_sample.astype(str).str.strip()
        count = len(values)
        fingerprint = {}
        for key, pattern in detectors.items():
            fingerprint[key] = round(float(values.str.match(pattern, na=False).mean()) if count else 0.0, 4)

        top_pattern = max(fingerprint, key=fingerprint.get) if fingerprint else None
        top_match_rate = float(fingerprint.get(top_pattern, 0.0)) if top_pattern else 0.0
        unique_ratio = float(values.nunique() / max(count, 1))
        avg_length = float(values.str.len().mean()) if count else 0.0

        if null_rate > 0.90:
            category = "sparse"
        elif top_match_rate >= 0.80:
            category = "typed"
        elif 0.40 <= top_match_rate < 0.80:
            category = "mixed"
        elif (
            unique_ratio > 0.80
            and avg_length > 20
            and top_match_rate < 0.40
            and data_type in {"varchar", "nvarchar", "text", "ntext"}
        ):
            category = "free_text"
        else:
            category = "opaque"

        return {
            "category": category,
            "top_pattern": top_pattern,
            "top_match_rate": round(top_match_rate, 4),
            "fingerprint": fingerprint,
            "unique_ratio": round(unique_ratio, 4),
            "avg_length": round(avg_length, 2),
            "null_rate": round(float(null_rate), 4),
        }

    @staticmethod
    def _get_context_warning(category: str, fingerprint: dict, null_rate: float) -> str | None:
        if category == "typed":
            return None
        if category == "sparse":
            return f"Only {int((1 - null_rate) * 100)}% of rows are non-null. Rules derived from limited sampled values."
        if category == "mixed":
            top = sorted(fingerprint.items(), key=lambda item: item[1], reverse=True)[:3]
            mix_text = ", ".join([f"{k} ({v:.0%})" for k, v in top if v > 0])
            return f"Column contains mixed value types: {mix_text}. Consider splitting into typed columns."
        if category == "free_text":
            return "No dominant pattern detected. Hygiene rules applied only."
        return "Column could not be classified. Minimum safe ruleset applied. Manual review recommended."

    @staticmethod
    def _semantic_signals(column_name):
        lowered = column_name.lower()
        signals = {
            "email": any(k in lowered for k in ("email", "mail")),
            "phone": any(k in lowered for k in ("phone", "mobile", "tel")),
            "ssn": any(k in lowered for k in ("ssn", "tax", "national_id")),
            "iso_date": any(k in lowered for k in ("dob", "birth", "date", "_at", "time")),
            "url": any(k in lowered for k in ("url", "website", "link")),
            "numeric": any(k in lowered for k in ("amount", "count", "qty", "num", "score", "price", "total")),
        }
        return signals

    @staticmethod
    def get_column_context(table: str, column: str) -> dict:
        if not ValidationService._is_safe_identifier(table) or not ValidationService._is_safe_identifier(column):
            return {
                "category": "opaque",
                "top_pattern": None,
                "top_match_rate": 0.0,
                "fingerprint": {},
                "unique_ratio": 0.0,
                "avg_length": 0.0,
                "null_rate": 0.0,
                "warning": "Unsafe table/column identifier rejected.",
            }

        schema = ValidationService.get_table_schema(table)
        schema_row = schema[schema["COLUMN_NAME"] == column] if not schema.empty else pd.DataFrame()
        if schema_row.empty:
            return {
                "category": "opaque",
                "top_pattern": None,
                "top_match_rate": 0.0,
                "fingerprint": {},
                "unique_ratio": 0.0,
                "avg_length": 0.0,
                "null_rate": 0.0,
                "warning": "Schema metadata not found for selected column.",
            }

        data_type = str(schema_row.iloc[0]["DATA_TYPE"]).lower()
        null_rate = ValidationService._fetch_null_rate(table, column)
        sample_df = ValidationService._fetch_non_null_sample(table, column)
        sample_series = sample_df["sample_value"] if not sample_df.empty else pd.Series(dtype="object")
        context = ValidationService._classify_column(
            data_type=data_type,
            null_rate=null_rate,
            non_null_sample=sample_series,
            detectors=ValidationService.PATTERN_DETECTORS,
        )
        context["warning"] = ValidationService._get_context_warning(
            context["category"], context["fingerprint"], context["null_rate"]
        )
        logger.info(
            "Column classification %s.%s -> category=%s top_pattern=%s top_match_rate=%.2f null_rate=%.2f",
            table,
            column,
            context["category"],
            context["top_pattern"],
            context["top_match_rate"],
            context["null_rate"],
        )
        return context

    @staticmethod
    def suggest_rules(table: str, column: str, sample_size: int = 200) -> list[dict]:
        """Suggest validation rules for a column using data-first classification and category branching."""
        if not ValidationService._is_safe_identifier(table) or not ValidationService._is_safe_identifier(column):
            return []

        schema = ValidationService.get_table_schema(table)
        if schema.empty:
            return []
        schema_row = schema[schema["COLUMN_NAME"] == column]
        if schema_row.empty:
            return []

        data_type = str(schema_row.iloc[0]["DATA_TYPE"]).lower()
        char_limit = schema_row.iloc[0]["CHARACTER_MAXIMUM_LENGTH"]
        char_limit = int(char_limit) if pd.notna(char_limit) and int(char_limit) > 0 else 4000

        null_rate = ValidationService._fetch_null_rate(table, column)
        sample_df = ValidationService._fetch_non_null_sample(
            table=table,
            column=column,
            target=min(max(int(sample_size), 1), 100),
            max_scan=2000,
        )
        sample_series = sample_df["sample_value"] if not sample_df.empty else pd.Series(dtype="object")
        value_strings = sample_series.astype(str).str.strip()
        non_null_count = len(value_strings)

        context = ValidationService._classify_column(
            data_type=data_type,
            null_rate=null_rate,
            non_null_sample=value_strings,
            detectors=ValidationService.PATTERN_DETECTORS,
        )
        context_warning = ValidationService._get_context_warning(
            context["category"], context["fingerprint"], context["null_rate"]
        )

        logger.info(
            "suggest_rules context for %s.%s: category=%s null_rate=%.2f top=%s(%.2f)",
            table, column, context["category"], context["null_rate"], context["top_pattern"], context["top_match_rate"]
        )

        suggestions = {}
        semantic_signals = ValidationService._semantic_signals(column)
        pattern_to_rule = {
            "email": "IsEmail",
            "phone": "is_phone",
            "ssn": "is_ssn",
            "iso_date": "IsDate",
            "url": "is_url",
            "integer": "is_digit",
            "decimal": "is_digit",
        }

        def add(rule_code, rule_params, confidence, rationale, source):
            ValidationService._upsert_suggestion(
                bucket=suggestions,
                rule_code=rule_code,
                rule_params=rule_params,
                confidence=round(float(confidence), 2),
                rationale=rationale,
                source=source,
            )

        # Step 7 branching
        if context["category"] == "sparse":
            for rule_code, rule_params, confidence, rationale in ValidationService.SPARSE_RULES:
                params = rule_params.format(char_limit=char_limit, null_pct=int(context["null_rate"] * 100))
                add(rule_code, params, confidence, rationale.format(null_pct=int(context["null_rate"] * 100)), "structural")
        elif context["category"] == "typed":
            for pattern_key, rule_code in pattern_to_rule.items():
                match_rate = context["fingerprint"].get(pattern_key, 0.0)
                if match_rate >= 0.80:
                    rule_params = "format=YYYY-MM-DD" if rule_code == "IsDate" else ""
                    if rule_code == "is_phone":
                        rule_params = "format=E164"
                    add(rule_code, rule_params, 0.72 + (0.2 * match_rate), f"Pattern detector `{pattern_key}` matched {match_rate:.0%} of sampled values.", "data")

            if data_type in ValidationService.NUMERIC_TYPES and non_null_count > 0:
                numeric_series = pd.to_numeric(value_strings, errors="coerce").dropna()
                if not numeric_series.empty:
                    q05 = float(numeric_series.quantile(0.05))
                    q95 = float(numeric_series.quantile(0.95))
                    add("is_digit", "", 0.87, "Numeric SQL data type detected from schema.", "structural")
                    add("min_value", f"value={q05:.4f}", 0.83, "5th percentile used as robust lower bound.", "data")
                    add("max_value", f"value={q95:.4f}", 0.83, "95th percentile used as robust upper bound.", "data")

            if context["null_rate"] <= 0.01:
                add("NOT_NULL", "", 0.8, "Full-table NULL rate is near zero.", "data")

            if non_null_count > 0:
                unique_values = sorted(value_strings.unique().tolist())
                unique_count = len(unique_values)
                distinct_ratio = unique_count / max(non_null_count, 1)
                if distinct_ratio <= 0.10 and unique_count < 15:
                    add("is_in_list", f"values={','.join(unique_values)}", 0.84, f"Low cardinality: {unique_count} distinct values over {non_null_count} non-null rows.", "data")

            if semantic_signals["email"]:
                add("IsEmail", "", 0.95, "Column name semantically indicates email.", "semantic")
            if semantic_signals["phone"]:
                add("is_phone", "format=E164", 0.92, "Column name semantically indicates phone.", "semantic")
            if semantic_signals["ssn"]:
                add("is_ssn", "", 0.92, "Column name semantically indicates identifier.", "semantic")
            if semantic_signals["iso_date"]:
                add("IsDate", "format=YYYY-MM-DD", 0.95, "Column name semantically indicates date/time.", "semantic")
            if semantic_signals["url"]:
                add("is_url", "", 0.9, "Column name semantically indicates URL.", "semantic")
        elif context["category"] == "mixed":
            for rule_code, rule_params, confidence, rationale in ValidationService.HYGIENE_RULES:
                add(rule_code, rule_params.format(char_limit=char_limit), confidence, f"MIXED CONTENT WARNING: {rationale}", "hygiene")
            add("record_structure_check", "", 0.75, "MIXED CONTENT WARNING: Mixed formats observed; enforce structural consistency.", "structural")
        elif context["category"] == "free_text":
            for rule_code, rule_params, confidence, rationale in ValidationService.HYGIENE_RULES:
                add(rule_code, rule_params.format(char_limit=char_limit), confidence, rationale, "hygiene")
        else:
            add("HasLength", f"max={char_limit}", 0.8, "Manual review required; applying only a safe length cap.", "structural")
            add("allow_null", "", 0.7, "Opaque column profile; allow null until type intent is clarified.", "structural")

        if context_warning:
            for suggestion in suggestions.values():
                suggestion["rationale"] = f"WARNING: {context_warning} | {suggestion['rationale']}"

        # Step 8 agreement scoring
        rule_signal_map = {
            "IsEmail": "email",
            "is_phone": "phone",
            "is_ssn": "ssn",
            "IsDate": "iso_date",
            "is_url": "url",
            "is_digit": "numeric",
            "min_value": "numeric",
            "max_value": "numeric",
        }
        for suggestion in suggestions.values():
            target_signal = rule_signal_map.get(suggestion["rule_code"])
            if not target_signal:
                continue
            implied = semantic_signals.get(target_signal, False)
            if implied:
                suggestion["confidence"] = round(min(0.99, suggestion["confidence"] * 1.10), 2)
                if suggestion["source"] == "data":
                    suggestion["source"] = "agreement"
                suggestion["rationale"] = f"{suggestion['rationale']} Name-data agreement boost applied."
            elif any(semantic_signals.values()):
                contradicts = any(
                    semantic_signals.get(signal, False) and signal != target_signal
                    for signal in ("email", "phone", "ssn", "iso_date", "url")
                )
                if contradicts:
                    suggestion["confidence"] = 0.0
                    suggestion["rationale"] = f"{suggestion['rationale']} Name-data contradiction detected; dropped."
                else:
                    suggestion["confidence"] = round(suggestion["confidence"] * 0.90, 2)
            else:
                suggestion["confidence"] = round(suggestion["confidence"] * 0.90, 2)

        filtered = [
            {
                "rule_code": s["rule_code"],
                "rule_params": s["rule_params"],
                "confidence": round(float(s["confidence"]), 2),
                "rationale": s["rationale"],
                "source": s["source"],
            }
            for s in suggestions.values()
            if round(float(s["confidence"]), 2) > 0.0
        ]
        return sorted(
            filtered,
            key=lambda item: item["confidence"],
            reverse=True,
        )
