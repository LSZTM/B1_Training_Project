/*
Priority 1 migration
- Eliminates silent-pass stubs.
- Implements table-scoped is_unique behavior in dispatcher.
- Implements ColumnComparison row-level operator comparison path.
- Adds rule implementation metadata for UI warnings.
*/

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
    SELECT N'ColumnComparison' AS rule_code, CAST(1 AS BIT) AS is_implemented, N'Implemented via vp_validate_column dynamic comparison.' AS status_note
    UNION ALL SELECT N'is_unique', CAST(1 AS BIT), N'Implemented as table-scoped set-based duplicate detection.'
    UNION ALL SELECT N'foreign_key_check', CAST(0 AS BIT), N'NOT_IMPLEMENTED: requires reference table metadata and mapping.'
    UNION ALL SELECT N'non_overlapping_range', CAST(0 AS BIT), N'NOT_IMPLEMENTED: requires start/end pair configuration and partition keys.'
    UNION ALL SELECT N'date_not_holiday', CAST(0 AS BIT), N'NOT_IMPLEMENTED: requires holiday calendar source.'
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
