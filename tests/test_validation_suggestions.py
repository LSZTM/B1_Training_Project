import unittest
from unittest.mock import patch

import pandas as pd

from services.validation_service import ValidationService


class ValidationSuggestionTests(unittest.TestCase):
    def _schema(self, column, data_type="varchar", char_max=255):
        return pd.DataFrame(
            [
                {
                    "COLUMN_NAME": column,
                    "DATA_TYPE": data_type,
                    "IS_NULLABLE": "NO",
                    "CHARACTER_MAXIMUM_LENGTH": char_max,
                }
            ]
        )

    def _sample(self, values):
        return pd.DataFrame({"sample_value": values})

    def test_exact_email_domain_match_suggests_email_rule(self):
        with (
            patch.object(ValidationService, "get_table_schema", return_value=self._schema("EmailAddress")),
            patch.object(ValidationService, "_fetch_null_rate", return_value=0.0),
            patch.object(
                ValidationService,
                "_fetch_non_null_sample",
                return_value=self._sample(["ada@example.com", "grace@example.org", "linus@example.net"]),
            ),
        ):
            suggestions = ValidationService.suggest_rules("Customers", "EmailAddress")

        by_code = {item["rule_code"]: item for item in suggestions}
        self.assertIn("IsEmail", by_code)
        self.assertGreaterEqual(by_code["IsEmail"]["confidence"], 0.95)
        self.assertIn(by_code["IsEmail"]["source"], {"domain", "agreement", "pattern"})

    def test_fixed_width_postal_code_suggests_format_and_exact_length(self):
        with (
            patch.object(ValidationService, "get_table_schema", return_value=self._schema("PostalCode", char_max=20)),
            patch.object(ValidationService, "_fetch_null_rate", return_value=0.0),
            patch.object(
                ValidationService,
                "_fetch_non_null_sample",
                return_value=self._sample(["02139", "10001", "30301", "94105"]),
            ),
        ):
            suggestions = ValidationService.suggest_rules("Customers", "PostalCode")

        by_code = {item["rule_code"]: item for item in suggestions}
        self.assertIn("is_postal_code_us", by_code)
        self.assertIn("exact_length", by_code)
        self.assertEqual(by_code["exact_length"]["rule_params"], "length=5")

    def test_token_matching_does_not_treat_paid_as_id(self):
        tokens = ValidationService._identifier_tokens("Invoices", "PaidDate")
        self.assertIn("paid", tokens)
        self.assertNotIn("id", tokens)
        self.assertFalse(
            ValidationService._rule_name_matches(
                ValidationService.RULE_SIGNAL_MAP["is_unique"],
                tokens,
                ValidationService._normalize_identifier("PaidDate"),
            )
        )


if __name__ == "__main__":
    unittest.main()
