/*
Configuration: Demo Sandbox Rules
- Injects rules into temp_validation_config for the demo_validation_sandbox table.
*/

DELETE FROM dbo.temp_validation_config WHERE table_name = 'demo_validation_sandbox';
GO

INSERT INTO dbo.temp_validation_config
(table_name, column_name, rule_code, rule_params, allow_null, error_code, is_active, primary_key_column, comparison_column)
VALUES
-- Format Rules
('demo_validation_sandbox', 'email', 'IsEmail', NULL, 1, 'F_EMAIL', 1, 'id', NULL),
('demo_validation_sandbox', 'ssn', 'is_ssn', NULL, 1, 'F_SSN', 1, 'id', NULL),
('demo_validation_sandbox', 'ip_address', 'is_ip_v4', NULL, 1, 'F_IPV4', 1, 'id', NULL),
('demo_validation_sandbox', 'phone', 'is_phone_e164', NULL, 1, 'F_PHONE', 1, 'id', NULL),

-- Range Rules
('demo_validation_sandbox', 'age', 'age_range', NULL, 1, 'R_AGE', 1, 'id', NULL),
('demo_validation_sandbox', 'price', 'positive_only', NULL, 1, 'R_POS', 1, 'id', NULL),

-- Spatial Rules
('demo_validation_sandbox', 'latitude', 'is_latitude', NULL, 1, 'S_LAT', 1, 'id', NULL),
('demo_validation_sandbox', 'longitude', 'is_longitude', NULL, 1, 'S_LON', 1, 'id', NULL),

-- Security Rules
('demo_validation_sandbox', 'json_payload', 'no_sql_injection', NULL, 1, 'SEC_SQLI', 1, 'id', NULL),
('demo_validation_sandbox', 'status_code', 'trimmed', NULL, 1, 'HYG_TRIM', 1, 'id', NULL),

-- Identity/Financial Rules
('demo_validation_sandbox', 'credit_card', 'luhn_check', NULL, 1, 'FIN_LUHN', 1, 'id', NULL),
('demo_validation_sandbox', 'iban', 'is_iban', NULL, 1, 'FIN_IBAN', 1, 'id', NULL),
('demo_validation_sandbox', 'status_code', 'exact_length', 'length=6', 1, 'ID_LEN', 1, 'id', NULL),

-- Logic Rules (Column Comparison)
('demo_validation_sandbox', 'end_date', 'ColumnComparison', 'operator=>,compare_to=start_date', 1, 'LOG_DATE', 1, 'id', 'start_date');
GO
