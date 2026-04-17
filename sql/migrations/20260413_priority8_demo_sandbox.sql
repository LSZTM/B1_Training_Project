/*
Priority 8 migration: Demo Validation Sandbox
- Creates a dedicated table for demonstration and testing of all validation functions.
- Uses NVARCHAR(MAX) exclusively to allow 'loose' data entry for testing dispatcher logic.
*/

IF OBJECT_ID('dbo.demo_validation_sandbox', 'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.demo_validation_sandbox;
END;
GO

CREATE TABLE dbo.demo_validation_sandbox
(
    id NVARCHAR(64) NOT NULL PRIMARY KEY,
    email NVARCHAR(MAX) NULL,
    ssn NVARCHAR(MAX) NULL,
    ip_address NVARCHAR(MAX) NULL,
    age NVARCHAR(MAX) NULL,
    phone NVARCHAR(MAX) NULL,
    credit_card NVARCHAR(MAX) NULL,
    iban NVARCHAR(MAX) NULL,
    latitude NVARCHAR(MAX) NULL,
    longitude NVARCHAR(MAX) NULL,
    json_payload NVARCHAR(MAX) NULL,
    price NVARCHAR(MAX) NULL,
    start_date NVARCHAR(MAX) NULL,
    end_date NVARCHAR(MAX) NULL,
    status_code NVARCHAR(MAX) NULL,
    created_at DATETIME NOT NULL DEFAULT GETDATE()
);
GO
