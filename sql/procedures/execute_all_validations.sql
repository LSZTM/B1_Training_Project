CREATE OR ALTER PROCEDURE dbo.execute_all_validations
    @table_filter NVARCHAR(MAX) = NULL -- Comma-separated list of tables
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE
        @table_name SYSNAME,
        @column_name SYSNAME,
        @rule_code NVARCHAR(128),
        @rule_params NVARCHAR(MAX),
        @allow_null BIT,
        @primary_key_column SYSNAME,
        @comparison_column SYSNAME,
        @error_code VARCHAR(10),
        @resolved_pk_column SYSNAME,
        @rows_scanned BIGINT,
        @before_errors INT,
        @after_errors INT,
        @fail_count INT,
        @pass_count INT,
        @duration_ms INT,
        @status NVARCHAR(32),
        @config_started DATETIME2(3),
        @sql NVARCHAR(MAX);

    DECLARE config_cursor CURSOR LOCAL FAST_FORWARD FOR
        SELECT
            table_name,
            column_name,
            rule_code,
            rule_params,
            ISNULL(allow_null, 0) AS allow_null,
            primary_key_column,
            comparison_column,
            ISNULL(error_code, 'E999') AS error_code
        FROM dbo.temp_validation_config
        WHERE ISNULL(is_active, 1) = 1
          AND (@table_filter IS NULL OR table_name IN (SELECT value FROM STRING_SPLIT(@table_filter, ',')))
        ORDER BY table_name, column_name, rule_code;

    OPEN config_cursor;
    FETCH NEXT FROM config_cursor INTO
        @table_name,
        @column_name,
        @rule_code,
        @rule_params,
        @allow_null,
        @primary_key_column,
        @comparison_column,
        @error_code;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        SET @config_started = SYSUTCDATETIME();
        SET @rows_scanned = 0;
        SET @before_errors = ISNULL((SELECT COUNT(*) FROM dbo.error_log), 0);
        SET @fail_count = 0;
        SET @pass_count = 0;
        SET @duration_ms = 0;
        SET @status = N'SUCCESS';

        BEGIN TRY
            IF NOT EXISTS (
                SELECT 1
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = @table_name
                  AND TABLE_TYPE = 'BASE TABLE'
            )
            BEGIN
                THROW 51001, 'Configured validation table does not exist.', 1;
            END;

            IF NOT EXISTS (
                SELECT 1
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = @table_name
                  AND COLUMN_NAME = @column_name
            )
            BEGIN
                THROW 51002, 'Configured validation column does not exist.', 1;
            END;

            IF @comparison_column IS NOT NULL
               AND NOT EXISTS (
                    SELECT 1
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = @table_name
                      AND COLUMN_NAME = @comparison_column
                )
            BEGIN
                THROW 51003, 'Configured comparison column does not exist.', 1;
            END;

            SET @resolved_pk_column = NULLIF(@primary_key_column, '');

            IF @resolved_pk_column IS NULL
            BEGIN
                SELECT TOP 1 @resolved_pk_column = c.name
                FROM sys.indexes i
                INNER JOIN sys.index_columns ic
                    ON i.object_id = ic.object_id
                   AND i.index_id = ic.index_id
                INNER JOIN sys.columns c
                    ON ic.object_id = c.object_id
                   AND ic.column_id = c.column_id
                WHERE i.is_primary_key = 1
                  AND i.object_id = OBJECT_ID(N'dbo.' + QUOTENAME(@table_name))
                ORDER BY ic.key_ordinal;
            END;

            SET @sql = N'SELECT @row_count = COUNT(*) FROM dbo.' + QUOTENAME(@table_name) + N';';
            EXEC sp_executesql @sql, N'@row_count BIGINT OUTPUT', @row_count = @rows_scanned OUTPUT;

            SET @sql = N'
                DECLARE
                    @record_id NVARCHAR(100),
                    @value NVARCHAR(4000),
                    @comparison_value NVARCHAR(4000);

                DECLARE row_cursor CURSOR LOCAL FAST_FORWARD FOR
                    SELECT '
                    + CASE
                        WHEN @resolved_pk_column IS NOT NULL THEN N'CAST(' + QUOTENAME(@resolved_pk_column) + N' AS NVARCHAR(100))'
                        ELSE N'CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS NVARCHAR(100))'
                      END
                    + N' AS record_id,
                           CAST(' + QUOTENAME(@column_name) + N' AS NVARCHAR(4000)) AS value,
                           '
                    + CASE
                        WHEN @comparison_column IS NOT NULL THEN N'CAST(' + QUOTENAME(@comparison_column) + N' AS NVARCHAR(4000))'
                        ELSE N'CAST(NULL AS NVARCHAR(4000))'
                      END
                    + N' AS comparison_value
                    FROM dbo.' + QUOTENAME(@table_name) + N';

                OPEN row_cursor;
                FETCH NEXT FROM row_cursor INTO @record_id, @value, @comparison_value;

                WHILE @@FETCH_STATUS = 0
                BEGIN
                    EXEC dbo.run_single_validation
                        @table_name = @table_name_param,
                        @record_id = @record_id,
                        @column_name = @column_name_param,
                        @rule_code = @rule_code_param,
                        @value = @value,
                        @rule_params = @rule_params_param,
                        @allow_null = @allow_null_param,
                        @comparison_value = @comparison_value,
                        @error_code_override = @error_code_param;

                    FETCH NEXT FROM row_cursor INTO @record_id, @value, @comparison_value;
                END;

                CLOSE row_cursor;
                DEALLOCATE row_cursor;
            ';

            EXEC sp_executesql
                @sql,
                N'@table_name_param SYSNAME, @column_name_param SYSNAME, @rule_code_param NVARCHAR(128), @rule_params_param NVARCHAR(MAX), @allow_null_param BIT, @error_code_param VARCHAR(10)',
                @table_name_param = @table_name,
                @column_name_param = @column_name,
                @rule_code_param = @rule_code,
                @rule_params_param = @rule_params,
                @allow_null_param = @allow_null,
                @error_code_param = @error_code;

            SET @after_errors = ISNULL((SELECT COUNT(*) FROM dbo.error_log), 0);
            SET @fail_count = @after_errors - @before_errors;
            SET @pass_count = CASE WHEN @rows_scanned > @fail_count THEN @rows_scanned - @fail_count ELSE 0 END;
            SET @duration_ms = DATEDIFF(MILLISECOND, @config_started, SYSUTCDATETIME());
            SET @status = CASE WHEN @fail_count > 0 THEN N'FAILED' ELSE N'SUCCESS' END;
        END TRY
        BEGIN CATCH
            SET @after_errors = ISNULL((SELECT COUNT(*) FROM dbo.error_log), 0);
            SET @fail_count = CASE WHEN @after_errors >= @before_errors THEN @after_errors - @before_errors ELSE 0 END;
            SET @pass_count = CASE WHEN @rows_scanned > @fail_count THEN @rows_scanned - @fail_count ELSE 0 END;
            SET @duration_ms = DATEDIFF(MILLISECOND, @config_started, SYSUTCDATETIME());
            SET @status = N'FAILED';
        END CATCH;

        INSERT INTO dbo.validation_run_history
        (
            table_name,
            column_name,
            rule_code,
            total_records_scanned,
            total_errors,
            duration_ms,
            status,
            run_timestamp
        )
        VALUES
        (
            @table_name,
            @column_name,
            @rule_code,
            @rows_scanned,
            @fail_count,
            @duration_ms,
            @status,
            SYSUTCDATETIME()
        );

        IF OBJECT_ID('dbo.validation_rule_results', 'U') IS NOT NULL
        BEGIN
            INSERT INTO dbo.validation_rule_results
            (
                run_id,
                table_name,
                column_name,
                rule_code,
                rows_scanned,
                pass_count,
                fail_count,
                pass_rate,
                run_timestamp
            )
            VALUES
            (
                SCOPE_IDENTITY(),
                @table_name,
                @column_name,
                @rule_code,
                @rows_scanned,
                @pass_count,
                @fail_count,
                CASE
                    WHEN @rows_scanned = 0 THEN CAST(0 AS DECIMAL(10,4))
                    ELSE CAST(CAST(@pass_count AS FLOAT) / NULLIF(@rows_scanned, 0) AS DECIMAL(10,4))
                END,
                SYSUTCDATETIME()
            );
        END;

        FETCH NEXT FROM config_cursor INTO
            @table_name,
            @column_name,
            @rule_code,
            @rule_params,
            @allow_null,
            @primary_key_column,
            @comparison_column,
            @error_code;
    END;

    CLOSE config_cursor;
    DEALLOCATE config_cursor;
END;
