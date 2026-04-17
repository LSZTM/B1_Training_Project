from __future__ import annotations

import json
import logging
import os
import traceback
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from utils.db import close_connection, get_connection

LOGGER = logging.getLogger(__name__)

SEVERITY_RANKS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}
DEFAULT_VISIBLE_SEVERITIES = ["INFO", "WARNING", "ERROR", "CRITICAL"]
VALIDATION_FAILURE_STATUSES = {"FAILED"}
VALIDATION_COMPLETION_STATUSES = {"PASSED", "FAILED", "COMPLETED"}
TIME_RANGE_OPTIONS = {
    "15m": {"label": "Last 15 minutes", "minutes": 15},
    "1h": {"label": "Last 1 hour", "minutes": 60},
    "6h": {"label": "Last 6 hours", "minutes": 360},
    "24h": {"label": "Last 24 hours", "minutes": 1440},
    "7d": {"label": "Last 7 days", "minutes": 10080},
}


@contextmanager
def db_conn():
    conn = get_connection()
    try:
        yield conn
    finally:
        close_connection(conn)


def normalize_severity(value: Any) -> str:
    candidate = str(value or "INFO").strip().upper()
    return candidate if candidate in SEVERITY_RANKS else "INFO"


def expand_minimum_severity(level: str | None) -> list[str]:
    normalized = normalize_severity(level or "INFO")
    threshold = SEVERITY_RANKS[normalized]
    return [name for name, rank in SEVERITY_RANKS.items() if rank >= threshold]


def resolve_effective_severities(
    mode: str = "explicit",
    explicit_levels: list[str] | None = None,
    minimum_level: str | None = None,
) -> list[str]:
    if mode == "minimum":
        return expand_minimum_severity(minimum_level)

    normalized = []
    for level in explicit_levels or DEFAULT_VISIBLE_SEVERITIES:
        candidate = normalize_severity(level)
        if candidate not in normalized:
            normalized.append(candidate)

    return normalized or DEFAULT_VISIBLE_SEVERITIES.copy()


def time_range_minutes(range_key: str | None) -> int:
    if range_key in TIME_RANGE_OPTIONS:
        return TIME_RANGE_OPTIONS[range_key]["minutes"]
    return TIME_RANGE_OPTIONS["1h"]["minutes"]


def safe_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def safe_json_dumps(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    try:
        return json.dumps(value, default=str, ensure_ascii=True, sort_keys=True, indent=2)
    except TypeError:
        return json.dumps(str(value), ensure_ascii=True)


def coerce_uuid(value: Any) -> str | None:
    if value in (None, ""):
        return None
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return None


def build_validation_context(record: dict[str, Any]) -> str | None:
    context = safe_text(record.get("validation_context"))
    if context:
        return context

    table_name = safe_text(record.get("table_name"))
    column_name = safe_text(record.get("column_name"))
    parts = [part for part in (table_name, column_name) if part]
    return ".".join(parts) if parts else None


def dataframe_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if frame.empty:
        return records

    for row in frame.where(pd.notnull(frame), None).to_dict(orient="records"):
        record = {}
        for key, value in row.items():
            if isinstance(value, pd.Timestamp):
                record[key] = value.isoformat()
            elif isinstance(value, datetime):
                record[key] = value.isoformat()
            else:
                record[key] = value
        records.append(record)
    return records


def apply_log_filters(
    frame: pd.DataFrame,
    *,
    search_text: str = "",
    severities: list[str] | None = None,
    validation_id: str = "",
    rule_filter: str = "",
    statuses: list[str] | None = None,
    time_range_key: str = "1h",
    show_only_failures: bool = False,
    now: datetime | None = None,
) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    filtered = frame.copy()
    filtered["severity"] = filtered["severity"].map(normalize_severity)
    filtered["severity_rank"] = filtered["severity"].map(SEVERITY_RANKS).fillna(SEVERITY_RANKS["INFO"])
    filtered["validation_status"] = filtered["validation_status"].fillna("").astype(str).str.upper()

    effective_severities = [normalize_severity(level) for level in (severities or DEFAULT_VISIBLE_SEVERITIES)]
    filtered = filtered[filtered["severity"].isin(effective_severities)]

    if show_only_failures:
        filtered = filtered[
            (filtered["validation_status"].isin(VALIDATION_FAILURE_STATUSES))
            | (filtered["severity_rank"] >= SEVERITY_RANKS["WARNING"])
        ]

    if validation_id:
        filtered = filtered[filtered["validation_id"].fillna("").astype(str) == validation_id.strip()]

    if rule_filter:
        candidate = rule_filter.strip().lower()
        rule_id_text = filtered.get("rule_id", pd.Series(dtype="object")).fillna("").astype(str).str.lower()
        rule_code_text = filtered.get("rule_code", pd.Series(dtype="object")).fillna("").astype(str).str.lower()
        filtered = filtered[(rule_id_text == candidate) | (rule_code_text == candidate)]

    if statuses:
        normalized_statuses = [str(status).strip().upper() for status in statuses if str(status).strip()]
        filtered = filtered[filtered["validation_status"].isin(normalized_statuses)]

    if "event_timestamp" in filtered.columns:
        timestamps = pd.to_datetime(filtered["event_timestamp"], utc=True, errors="coerce")
        current_time = now or datetime.now(timezone.utc)
        earliest_time = current_time - timedelta(minutes=time_range_minutes(time_range_key))
        filtered = filtered[timestamps >= earliest_time]

    if search_text:
        term = search_text.strip().lower()
        if term:
            search_columns = [
                "message",
                "source_module",
                "validation_id",
                "correlation_id",
                "request_id",
                "rule_id",
                "rule_code",
                "entity_id",
                "record_id",
                "table_name",
                "column_name",
                "validation_context",
                "validation_status",
                "exception_type",
                "payload_json",
            ]
            search_frame = filtered.reindex(columns=search_columns, fill_value="").fillna("").astype(str)
            mask = search_frame.apply(lambda column: column.str.lower().str.contains(term, regex=False))
            filtered = filtered[mask.any(axis=1)]

    return filtered.copy()


def summarize_logs(frame: pd.DataFrame, *, live_mode: bool, connected: bool) -> dict[str, Any]:
    summary = {
        "total_events": 0,
        "critical_count": 0,
        "error_count": 0,
        "warning_count": 0,
        "running_validations": 0,
        "failed_validations": 0,
        "avg_duration_ms": 0,
        "live_status": "DISCONNECTED" if not connected else "LIVE" if live_mode else "PAUSED",
    }

    if frame.empty:
        return summary

    working = frame.copy()
    working["severity"] = working["severity"].map(normalize_severity)
    working["validation_status"] = working["validation_status"].fillna("").astype(str).str.upper()
    working["duration_ms"] = pd.to_numeric(working["duration_ms"], errors="coerce")

    summary["total_events"] = int(len(working))
    summary["critical_count"] = int((working["severity"] == "CRITICAL").sum())
    summary["error_count"] = int((working["severity"] == "ERROR").sum())
    summary["warning_count"] = int((working["severity"] == "WARNING").sum())

    if "validation_id" in working.columns:
        validation_statuses = (
            working[working["validation_id"].notna()]
            .groupby("validation_id")["validation_status"]
            .agg(list)
            .to_dict()
        )
        running = 0
        failed = 0
        for statuses in validation_statuses.values():
            status_set = set(status for status in statuses if status)
            if "FAILED" in status_set:
                failed += 1
            if "STARTED" in status_set and not status_set.intersection(VALIDATION_COMPLETION_STATUSES):
                running += 1
        summary["running_validations"] = running
        summary["failed_validations"] = failed

    valid_duration_rows = working["duration_ms"].dropna()
    if not valid_duration_rows.empty:
        summary["avg_duration_ms"] = int(round(valid_duration_rows.mean()))

    return summary


class LogsService:
    TABLE_NAME = "dbo.validation_logs"
    WRAPPER_PROCEDURE = "dbo.execute_all_validations_with_logging"
    FIXTURE_PATH = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "validation_logs_fixture.json"

    @staticmethod
    def fixture_mode_enabled() -> bool:
        return os.getenv("DATAGUARD_LOGS_FIXTURE", "0") == "1"

    @staticmethod
    def schema_state() -> dict[str, bool]:
        try:
            with db_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT
                        CASE WHEN OBJECT_ID('dbo.validation_logs', 'U') IS NULL THEN 0 ELSE 1 END AS logs_ready,
                        CASE WHEN OBJECT_ID('dbo.execute_all_validations_with_logging', 'P') IS NULL THEN 0 ELSE 1 END AS wrapper_ready
                    OPTION (RECOMPILE)
                    """
                )
                row = cursor.fetchone()
            return {
                "logs_ready": bool(row[0]) if row else False,
                "wrapper_ready": bool(row[1]) if row else False,
            }
        except Exception:
            return {"logs_ready": False, "wrapper_ready": False}

    @staticmethod
    def load_fixture_dataframe() -> pd.DataFrame:
        if not LogsService.FIXTURE_PATH.exists():
            return pd.DataFrame()
        try:
            data = json.loads(LogsService.FIXTURE_PATH.read_text(encoding="utf-8"))
            frame = pd.DataFrame(data)
            if not frame.empty and "event_timestamp" in frame.columns:
                frame["event_timestamp"] = pd.to_datetime(frame["event_timestamp"], utc=True, errors="coerce")
            return frame
        except Exception:
            return pd.DataFrame()

    @staticmethod
    def fetch_logs(
        *,
        limit: int = 600,
        time_range_key: str = "1h",
        search_text: str = "",
        severity_mode: str = "explicit",
        explicit_severities: list[str] | None = None,
        minimum_severity: str | None = None,
        validation_id: str = "",
        rule_filter: str = "",
        statuses: list[str] | None = None,
        show_only_failures: bool = False,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        effective_severities = resolve_effective_severities(
            mode=severity_mode,
            explicit_levels=explicit_severities,
            minimum_level=minimum_severity,
        )

        metadata = {
            "connected": True,
            "schema_ready": True,
            "effective_severities": effective_severities,
            "error": None,
        }

        if LogsService.fixture_mode_enabled():
            frame = LogsService.load_fixture_dataframe()
            filtered = apply_log_filters(
                frame,
                search_text=search_text,
                severities=effective_severities,
                validation_id=validation_id,
                rule_filter=rule_filter,
                statuses=statuses,
                time_range_key=time_range_key,
                show_only_failures=show_only_failures,
            )
            return filtered.sort_values(by=["event_timestamp", "log_id"], ascending=[False, False]), metadata

        state = LogsService.schema_state()
        metadata["schema_ready"] = state["logs_ready"]
        if not state["logs_ready"]:
            metadata["connected"] = True
            metadata["error"] = "validation_logs table is not installed."
            return pd.DataFrame(), metadata

        query = [
            """
            SELECT TOP (?) 
                log_id,
                event_timestamp,
                severity,
                severity_rank,
                event_type,
                message,
                source_module,
                CONVERT(VARCHAR(36), validation_id) AS validation_id,
                CONVERT(VARCHAR(36), correlation_id) AS correlation_id,
                request_id,
                run_id,
                rule_id,
                rule_code,
                entity_id,
                record_id,
                table_name,
                column_name,
                validation_context,
                validation_status,
                duration_ms,
                exception_type,
                stack_trace,
                input_summary,
                output_summary,
                payload_json
            FROM dbo.validation_logs WITH (NOLOCK)
            WHERE event_timestamp >= DATEADD(MINUTE, -?, SYSUTCDATETIME())
            """
        ]
        params: list[Any] = [int(limit), time_range_minutes(time_range_key)]

        if effective_severities:
            placeholders = ", ".join("?" for _ in effective_severities)
            query.append(f" AND severity IN ({placeholders})")
            params.extend(effective_severities)

        if validation_id:
            query.append(" AND CONVERT(VARCHAR(36), validation_id) = ?")
            params.append(validation_id.strip())

        if rule_filter:
            candidate = rule_filter.strip()
            query.append(" AND (CAST(rule_id AS NVARCHAR(32)) = ? OR rule_code = ?)")
            params.extend([candidate, candidate])

        if statuses:
            normalized_statuses = [str(status).strip().upper() for status in statuses if str(status).strip()]
            if normalized_statuses:
                placeholders = ", ".join("?" for _ in normalized_statuses)
                query.append(f" AND UPPER(ISNULL(validation_status, '')) IN ({placeholders})")
                params.extend(normalized_statuses)

        if show_only_failures:
            query.append(
                """
                AND (
                    UPPER(ISNULL(validation_status, '')) = 'FAILED'
                    OR severity_rank >= ?
                )
                """
            )
            params.append(SEVERITY_RANKS["WARNING"])

        if search_text.strip():
            like_value = f"%{search_text.strip()}%"
            query.append(
                """
                AND (
                    message LIKE ?
                    OR source_module LIKE ?
                    OR CONVERT(VARCHAR(36), validation_id) LIKE ?
                    OR CONVERT(VARCHAR(36), correlation_id) LIKE ?
                    OR ISNULL(request_id, '') LIKE ?
                    OR ISNULL(CAST(rule_id AS NVARCHAR(32)), '') LIKE ?
                    OR ISNULL(rule_code, '') LIKE ?
                    OR ISNULL(entity_id, '') LIKE ?
                    OR ISNULL(record_id, '') LIKE ?
                    OR ISNULL(table_name, '') LIKE ?
                    OR ISNULL(column_name, '') LIKE ?
                    OR ISNULL(validation_context, '') LIKE ?
                    OR ISNULL(exception_type, '') LIKE ?
                    OR ISNULL(payload_json, '') LIKE ?
                )
                """
            )
            params.extend([like_value] * 14)

        query.append(" ORDER BY event_timestamp DESC, log_id DESC")

        try:
            with db_conn() as conn:
                frame = pd.read_sql("".join(query), conn, params=params)
            if not frame.empty:
                frame["event_timestamp"] = pd.to_datetime(frame["event_timestamp"], utc=True, errors="coerce")
            return frame, metadata
        except Exception as exc:
            metadata["connected"] = False
            metadata["error"] = str(exc)
            return pd.DataFrame(), metadata

    @staticmethod
    def log_event(
        *,
        severity: str,
        message: str,
        event_type: str,
        source_module: str,
        validation_id: str | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
        run_id: int | None = None,
        rule_id: int | None = None,
        rule_code: str | None = None,
        entity_id: str | None = None,
        record_id: str | None = None,
        table_name: str | None = None,
        column_name: str | None = None,
        validation_context: str | None = None,
        validation_status: str | None = None,
        duration_ms: int | None = None,
        payload: Any = None,
        input_summary: Any = None,
        output_summary: Any = None,
        exception_type: str | None = None,
        stack_trace: str | None = None,
    ) -> dict[str, Any]:
        normalized_severity = normalize_severity(severity)
        normalized_validation_id = coerce_uuid(validation_id)
        normalized_correlation_id = coerce_uuid(correlation_id) or str(uuid.uuid4())
        if event_type.startswith("validation.") and not normalized_validation_id:
            normalized_validation_id = str(uuid.uuid4())

        record = {
            "message": safe_text(message) or "Validation event",
            "event_type": safe_text(event_type) or "validation.event",
            "source_module": safe_text(source_module) or "application",
            "validation_id": normalized_validation_id,
            "correlation_id": normalized_correlation_id,
            "request_id": safe_text(request_id),
            "run_id": run_id,
            "rule_id": rule_id,
            "rule_code": safe_text(rule_code),
            "entity_id": safe_text(entity_id),
            "record_id": safe_text(record_id),
            "table_name": safe_text(table_name),
            "column_name": safe_text(column_name),
            "validation_context": safe_text(validation_context),
            "validation_status": safe_text(validation_status).upper() if safe_text(validation_status) else None,
            "duration_ms": duration_ms,
            "exception_type": safe_text(exception_type),
            "stack_trace": safe_text(stack_trace),
            "input_summary": safe_json_dumps(input_summary),
            "output_summary": safe_json_dumps(output_summary),
            "payload_json": safe_json_dumps(payload),
        }
        record["validation_context"] = build_validation_context(record)

        state = LogsService.schema_state()
        if not state["logs_ready"]:
            LOGGER.warning("Structured log skipped because validation_logs is not installed: %s", record["message"])
            return {
                "success": False,
                "validation_id": normalized_validation_id,
                "correlation_id": normalized_correlation_id,
                "reason": "schema_not_ready",
            }

        try:
            with db_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO dbo.validation_logs
                    (
                        severity,
                        event_type,
                        message,
                        source_module,
                        validation_id,
                        correlation_id,
                        request_id,
                        run_id,
                        rule_id,
                        rule_code,
                        entity_id,
                        record_id,
                        table_name,
                        column_name,
                        validation_context,
                        validation_status,
                        duration_ms,
                        exception_type,
                        stack_trace,
                        input_summary,
                        output_summary,
                        payload_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    normalized_severity,
                    record["event_type"],
                    record["message"],
                    record["source_module"],
                    record["validation_id"],
                    record["correlation_id"],
                    record["request_id"],
                    record["run_id"],
                    record["rule_id"],
                    record["rule_code"],
                    record["entity_id"],
                    record["record_id"],
                    record["table_name"],
                    record["column_name"],
                    record["validation_context"],
                    record["validation_status"],
                    record["duration_ms"],
                    record["exception_type"],
                    record["stack_trace"],
                    record["input_summary"],
                    record["output_summary"],
                    record["payload_json"],
                )
                conn.commit()
            return {
                "success": True,
                "validation_id": record["validation_id"],
                "correlation_id": record["correlation_id"],
            }
        except Exception as exc:
            LOGGER.critical(
                "Structured log write failed: severity=%s event_type=%s message=%s error=%s",
                normalized_severity,
                record["event_type"],
                record["message"],
                exc,
            )
            return {
                "success": False,
                "validation_id": record["validation_id"],
                "correlation_id": record["correlation_id"],
                "reason": str(exc),
            }

    @staticmethod
    def capture_exception(
        *,
        message: str,
        source_module: str,
        exception: Exception,
        severity: str = "ERROR",
        event_type: str = "validation.exception",
        payload: Any = None,
        validation_id: str | None = None,
        correlation_id: str | None = None,
        validation_status: str | None = "FAILED",
    ) -> dict[str, Any]:
        return LogsService.log_event(
            severity=severity,
            message=message,
            event_type=event_type,
            source_module=source_module,
            validation_id=validation_id,
            correlation_id=correlation_id,
            validation_status=validation_status,
            payload=payload,
            exception_type=type(exception).__name__,
            stack_trace="".join(traceback.format_exception(type(exception), exception, exception.__traceback__)),
        )
