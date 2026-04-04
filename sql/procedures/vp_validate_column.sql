CREATE OR ALTER PROCEDURE dbo.vp_validate_column
    @table_name NVARCHAR(128),
    @column_name NVARCHAR(128),
    @rule_code NVARCHAR(64),
    @param NVARCHAR(MAX) = NULL,
    @sample_size INT = 1000
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @pass_count INT = 0, @fail_count INT = 0, @scanned INT = 0;
    DECLARE @fn SYSNAME = N'dbo.vf_' + @rule_code;
    DECLARE @sql NVARCHAR(MAX);
    DECLARE @comparison_column NVARCHAR(128);

    IF @rule_code = N'ColumnComparison'
    BEGIN
        SELECT TOP 1 @comparison_column = comparison_column
        FROM dbo.temp_validation_config
        WHERE table_name = @table_name
          AND column_name = @column_name
          AND rule_code = @rule_code
          AND is_active = 1
        ORDER BY id DESC;

        IF @comparison_column IS NULL
            THROW 50002, 'ColumnComparison rule requires comparison_column.', 1;

        SET @sql = N'
        ;WITH sample_data AS (
            SELECT TOP (@top_n) ' + QUOTENAME(@column_name) + N' AS left_v, ' + QUOTENAME(@comparison_column) + N' AS right_v
            FROM ' + QUOTENAME(@table_name) + N'
        )
        SELECT
            @pass_count = SUM(CASE
                WHEN left_v IS NULL OR right_v IS NULL THEN 1
                WHEN @op = ''>''  AND left_v > right_v THEN 1
                WHEN @op = ''<''  AND left_v < right_v THEN 1
                WHEN @op = ''>='' AND left_v >= right_v THEN 1
                WHEN @op = ''<='' AND left_v <= right_v THEN 1
                WHEN @op = ''!='' AND left_v <> right_v THEN 1
                WHEN @op = ''=''  AND left_v = right_v THEN 1
                ELSE 0
            END),
            @fail_count = SUM(CASE
                WHEN left_v IS NULL OR right_v IS NULL THEN 0
                WHEN @op = ''>''  AND left_v > right_v THEN 0
                WHEN @op = ''<''  AND left_v < right_v THEN 0
                WHEN @op = ''>='' AND left_v >= right_v THEN 0
                WHEN @op = ''<='' AND left_v <= right_v THEN 0
                WHEN @op = ''!='' AND left_v <> right_v THEN 0
                WHEN @op = ''=''  AND left_v = right_v THEN 0
                ELSE 1
            END),
            @scanned = COUNT(*)
        FROM sample_data;';

        DECLARE @operator NVARCHAR(4) = '=';
        IF @param IS NOT NULL AND CHARINDEX('operator=', @param) > 0
        BEGIN
            DECLARE @op_start INT = CHARINDEX('operator=', @param) + LEN('operator=');
            DECLARE @op_end INT = CHARINDEX(',', @param + ',', @op_start);
            SET @operator = LTRIM(RTRIM(SUBSTRING(@param, @op_start, @op_end - @op_start)));
        END

        IF @operator NOT IN ('>', '<', '>=', '<=', '=', '!=')
            THROW 50003, 'Unsupported ColumnComparison operator.', 1;

        EXEC sp_executesql
            @sql,
            N'@top_n INT, @op NVARCHAR(4), @pass_count INT OUTPUT, @fail_count INT OUTPUT, @scanned INT OUTPUT',
            @top_n = @sample_size,
            @op = @operator,
            @pass_count = @pass_count OUTPUT,
            @fail_count = @fail_count OUTPUT,
            @scanned = @scanned OUTPUT;
    END
    ELSE IF @rule_code = N'is_unique'
    BEGIN
        SET @sql = N'
        ;WITH sample_data AS (
            SELECT TOP (@top_n) CAST(' + QUOTENAME(@column_name) + N' AS NVARCHAR(MAX)) AS v
            FROM ' + QUOTENAME(@table_name) + N'
        ),
        duplicate_keys AS (
            SELECT v
            FROM sample_data
            WHERE v IS NOT NULL
            GROUP BY v
            HAVING COUNT(*) > 1
        )
        SELECT
            @fail_count = SUM(CASE WHEN d.v IS NULL THEN 0 ELSE 1 END),
            @pass_count = SUM(CASE WHEN d.v IS NULL THEN 1 ELSE 0 END),
            @scanned = COUNT(*)
        FROM sample_data s
        LEFT JOIN duplicate_keys d
            ON s.v = d.v;';

        EXEC sp_executesql
            @sql,
            N'@top_n INT, @pass_count INT OUTPUT, @fail_count INT OUTPUT, @scanned INT OUTPUT',
            @top_n = @sample_size,
            @pass_count = @pass_count OUTPUT,
            @fail_count = @fail_count OUTPUT,
            @scanned = @scanned OUTPUT;
    END
    ELSE
    BEGIN
        IF OBJECT_ID(@fn, 'FN') IS NULL
            THROW 50001, 'Validation function not found for rule_code', 1;

        SET @sql = N'
        ;WITH sample_data AS (
            SELECT TOP (@top_n) CAST(' + QUOTENAME(@column_name) + N' AS NVARCHAR(MAX)) AS v
            FROM ' + QUOTENAME(@table_name) + N'
        )
        SELECT
            @pass_count = SUM(CASE WHEN ' + @fn + N'(v' + CASE WHEN @param IS NULL THEN N'' ELSE N', @p' END + N') = 1 THEN 1 ELSE 0 END),
            @fail_count = SUM(CASE WHEN ' + @fn + N'(v' + CASE WHEN @param IS NULL THEN N'' ELSE N', @p' END + N') = 0 THEN 1 ELSE 0 END),
            @scanned = COUNT(*)
        FROM sample_data;';

        EXEC sp_executesql
            @sql,
            N'@top_n INT, @p NVARCHAR(MAX), @pass_count INT OUTPUT, @fail_count INT OUTPUT, @scanned INT OUTPUT',
            @top_n = @sample_size,
            @p = @param,
            @pass_count = @pass_count OUTPUT,
            @fail_count = @fail_count OUTPUT,
            @scanned = @scanned OUTPUT;
    END

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
