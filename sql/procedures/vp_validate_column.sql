CREATE OR ALTER PROCEDURE dbo.vp_validate_column
    @table_name NVARCHAR(128),
    @column_name NVARCHAR(128),
    @rule_code NVARCHAR(64),
    @param NVARCHAR(MAX) = NULL,
    @sample_size INT = 1000
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @fn SYSNAME = N'dbo.vf_' + @rule_code;
    IF OBJECT_ID(@fn, 'FN') IS NULL
        THROW 50001, 'Validation function not found for rule_code', 1;

    DECLARE @sql NVARCHAR(MAX) = N'
    ;WITH sample_data AS (
        SELECT TOP (@top_n) CAST(' + QUOTENAME(@column_name) + N' AS NVARCHAR(MAX)) AS v
        FROM ' + QUOTENAME(@table_name) + N'
    )
    SELECT
        @pass_count = SUM(CASE WHEN ' + @fn + N'(v' + CASE WHEN @param IS NULL THEN N'' ELSE N', @p' END + N') = 1 THEN 1 ELSE 0 END),
        @fail_count = SUM(CASE WHEN ' + @fn + N'(v' + CASE WHEN @param IS NULL THEN N'' ELSE N', @p' END + N') = 0 THEN 1 ELSE 0 END),
        @scanned = COUNT(*)
    FROM sample_data;';

    DECLARE @pass_count INT = 0, @fail_count INT = 0, @scanned INT = 0;

    EXEC sp_executesql
        @sql,
        N'@top_n INT, @p NVARCHAR(MAX), @pass_count INT OUTPUT, @fail_count INT OUTPUT, @scanned INT OUTPUT',
        @top_n = @sample_size,
        @p = @param,
        @pass_count = @pass_count OUTPUT,
        @fail_count = @fail_count OUTPUT,
        @scanned = @scanned OUTPUT;

    INSERT INTO dbo.validation_run_history
    (
        table_name, column_name, rule_code, total_records_scanned, total_errors, status, run_timestamp
    )
    VALUES
    (
        @table_name, @column_name, @rule_code, @scanned, @fail_count,
        CASE WHEN @fail_count = 0 THEN 'SUCCESS' ELSE 'FAILED' END,
        GETDATE()
    );

    SELECT
        @table_name AS table_name,
        @column_name AS column_name,
        @rule_code AS rule_code,
        @scanned AS rows_scanned,
        @pass_count AS pass_count,
        @fail_count AS fail_count,
        CAST(CASE WHEN @scanned = 0 THEN 0 ELSE 1.0 * @pass_count / @scanned END AS DECIMAL(10,4)) AS pass_rate;
END
