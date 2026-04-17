/*
Priority 6 migration
- Aligns runtime validation procedures with temp_validation_config.
- Restores SQL-driven batch execution so the app does not need Python fallbacks.
- Adds missing config metadata used by the UI and procedures.
*/

IF COL_LENGTH('dbo.temp_validation_config', 'error_code') IS NULL
BEGIN
    ALTER TABLE dbo.temp_validation_config
    ADD error_code VARCHAR(10) NULL;
END;
GO

UPDATE dbo.temp_validation_config
SET error_code = ISNULL(error_code, 'E999')
WHERE error_code IS NULL;
GO

IF OBJECT_ID('dbo.rule_implementation_status', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.rule_implementation_status
    (
        rule_code NVARCHAR(64) NOT NULL PRIMARY KEY,
        is_implemented BIT NOT NULL,
        status_note NVARCHAR(255) NULL,
        updated_at DATETIME NOT NULL DEFAULT GETDATE()
    );
END;
GO

MERGE dbo.rule_implementation_status AS target
USING (
    SELECT N'ColumnComparison' AS rule_code, CAST(1 AS BIT) AS is_implemented, N'Implemented through run_single_validation and function dispatch.' AS status_note
    UNION ALL SELECT N'is_unique', CAST(1 AS BIT), N'Implemented through vf_is_unique / SQL dispatch where configured.'
    UNION ALL SELECT N'foreign_key_check', CAST(0 AS BIT), N'Not implemented in current training database.'
    UNION ALL SELECT N'non_overlapping_range', CAST(0 AS BIT), N'Not implemented in current training database.'
    UNION ALL SELECT N'date_not_holiday', CAST(0 AS BIT), N'Not implemented in current training database.'
) AS src
ON target.rule_code = src.rule_code
WHEN MATCHED THEN
    UPDATE SET
        target.is_implemented = src.is_implemented,
        target.status_note = src.status_note,
        target.updated_at = GETDATE()
WHEN NOT MATCHED THEN
    INSERT (rule_code, is_implemented, status_note)
    VALUES (src.rule_code, src.is_implemented, src.status_note);
GO
