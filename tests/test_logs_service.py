import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from services.logs_service import (
    DEFAULT_VISIBLE_SEVERITIES,
    apply_log_filters,
    resolve_effective_severities,
    summarize_logs,
)


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "validation_logs_fixture.json"


def load_fixture_frame() -> pd.DataFrame:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    frame = pd.DataFrame(data)
    frame["event_timestamp"] = pd.to_datetime(frame["event_timestamp"], utc=True, errors="coerce")
    return frame


class LogsServiceTests(unittest.TestCase):
    def setUp(self):
        self.frame = load_fixture_frame()
        self.now = datetime(2026, 4, 13, 0, 8, tzinfo=timezone.utc)

    def test_default_view_hides_debug(self):
        filtered = apply_log_filters(
            self.frame,
            severities=DEFAULT_VISIBLE_SEVERITIES,
            time_range_key="24h",
            now=self.now,
        )
        self.assertNotIn("DEBUG", filtered["severity"].tolist())
        self.assertIn("ERROR", filtered["severity"].tolist())

    def test_minimum_severity_warning_includes_warning_and_above(self):
        severities = resolve_effective_severities(mode="minimum", minimum_level="WARNING")
        filtered = apply_log_filters(
            self.frame,
            severities=severities,
            time_range_key="24h",
            now=self.now,
        )
        self.assertEqual(severities, ["WARNING", "ERROR", "CRITICAL"])
        self.assertNotIn("INFO", filtered["severity"].tolist())
        self.assertNotIn("DEBUG", filtered["severity"].tolist())
        self.assertIn("CRITICAL", filtered["severity"].tolist())

    def test_failure_only_focuses_on_failed_and_high_signal_events(self):
        filtered = apply_log_filters(
            self.frame,
            severities=DEFAULT_VISIBLE_SEVERITIES,
            time_range_key="24h",
            show_only_failures=True,
            now=self.now,
        )
        messages = filtered["message"].tolist()
        self.assertIn("Validation failed for Customers.Email using NOT_NULL.", messages)
        self.assertIn("Validation engine unavailable during dependency outage.", messages)
        self.assertNotIn("Validation passed for Orders.OrderCode using HasLength.", messages)

    def test_summary_counts_live_state_failures_and_running_validations(self):
        filtered = apply_log_filters(
            self.frame,
            severities=["INFO", "WARNING", "ERROR", "CRITICAL"],
            time_range_key="24h",
            now=self.now,
        )
        summary = summarize_logs(filtered, live_mode=True, connected=True)
        self.assertEqual(summary["live_status"], "LIVE")
        self.assertEqual(summary["critical_count"], 1)
        self.assertEqual(summary["error_count"], 1)
        self.assertEqual(summary["warning_count"], 1)
        self.assertEqual(summary["failed_validations"], 2)
        self.assertEqual(summary["running_validations"], 1)
        self.assertGreater(summary["avg_duration_ms"], 0)

    def test_validation_id_filter_preserves_single_journey(self):
        filtered = apply_log_filters(
            self.frame,
            severities=["INFO", "WARNING", "ERROR", "CRITICAL"],
            validation_id="33333333-3333-3333-3333-333333333333",
            time_range_key="24h",
            now=self.now,
        )
        validation_ids = filtered["validation_id"].dropna().unique().tolist()
        self.assertEqual(validation_ids, ["33333333-3333-3333-3333-333333333333"])
        self.assertTrue((filtered["validation_status"].isin(["COMPLETED", "PASSED"])).all())


if __name__ == "__main__":
    unittest.main()
