/*
Demo Seed: Validation Sandbox Data
- Row 'GOLD-001': 100% Valid Data (Golden Row)
- Row 'FAIL-001': Format Violations (Email, SSN, IP, Phone)
- Row 'FAIL-002': Range Violations (Age, Percentage, Coordinates)
- Row 'FAIL-003': Security Violations (SQL Injection, PII)
- Row 'FAIL-004': Financial/Identity Violations (IBAN, Credit Card, Fixed Length)
- Row 'FAIL-005': Temporal/Logical Violations (Dates, Comparison)
*/

TRUNCATE TABLE dbo.demo_validation_sandbox;
GO

INSERT INTO dbo.demo_validation_sandbox
(id, email, ssn, ip_address, age, phone, credit_card, iban, latitude, longitude, json_payload, price, start_date, end_date, status_code)
VALUES
-- Golden Row (Passes All)
(
    'GOLD-001', 
    'valid.user@example.com', 
    '999-00-1111', 
    '192.168.1.1', 
    '25', 
    '+12345678901', 
    '4111111111111111', 
    'GB29NWBK60161331926819', 
    '40.7128', 
    '-74.0060', 
    '{"status": "active", "version": 1.0}', 
    '99.99', 
    '2024-01-01', 
    '2024-12-31', 
    'ACTIVE'
),
-- Format Failures
(
    'FAIL-001', 
    'invalid-email-at-sign', 
    '12-345-678', 
    '999.999.999.999', 
    '30', 
    '123-abc-456', 
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
),
-- Range Failures
(
    'FAIL-002', 
    'range@test.com', 
    NULL, NULL, 
    '250', -- Age too high
    NULL, NULL, NULL, 
    '105.0', -- Latitude out of range
    '-200.0', -- Longitude out of range
    NULL, 
    '-50.0', -- Price should be positive
    NULL, NULL, NULL
),
-- Security Failures
(
    'FAIL-003', 
    'hacker@exploit.org', 
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    '{"data": "normal", "attack": "SELECT * FROM users; --"}', -- SQL Injection pattern
    NULL, NULL, NULL, 
    '   TrimMe   ' -- Leading/Trailing white space
),
-- Identity/Financial Failures
(
    'FAIL-004', 
    'finance@test.com', 
    NULL, NULL, NULL, NULL, 
    '1234123412341238', -- Bad Luhn checksum
    'DE1234567890', -- Short IBAN
    NULL, NULL, NULL, NULL, NULL, NULL, 
    'SHORT' -- Suppose we want exact length
),
-- Temporal/Logic Failures
(
    'FAIL-005', 
    'date@test.com', 
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    '2025-01-01', -- Start Date
    '2024-01-01', -- End Date (Earlier than Start Date)
    NULL
);
GO
