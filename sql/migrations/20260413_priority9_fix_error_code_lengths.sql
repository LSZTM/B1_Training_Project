/*
Priority 9 migration: Fix error code truncation
- Increases error_code column size in temp_validation_config and error_log.
- Prevents failures when adding rules with auto-generated names (e.g., 'AUTO_PERCENTAGE_RANGE').
*/

-- Fix temp_validation_config
IF COL_LENGTH('dbo.temp_validation_config', 'error_code') IS NOT NULL
BEGIN
    ALTER TABLE dbo.temp_validation_config
    ALTER COLUMN error_code VARCHAR(50) NULL;
END;
GO

-- Fix error_log
IF COL_LENGTH('dbo.error_log', 'error_code') IS NOT NULL
BEGIN
    ALTER TABLE dbo.error_log
    ALTER COLUMN error_code VARCHAR(50) NULL;
END;
GO
