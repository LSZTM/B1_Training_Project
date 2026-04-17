CREATE OR ALTER PROCEDURE dbo.run_single_validation
    @table_name SYSNAME,
    @record_id NVARCHAR(100),
    @column_name SYSNAME,
    @rule_code NVARCHAR(128),
    @value NVARCHAR(4000),
    @rule_params NVARCHAR(MAX) = NULL,
    @allow_null BIT = 0,
    @comparison_value NVARCHAR(4000) = NULL,
    @error_code_override VARCHAR(10) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE
        @is_valid BIT = 1,
        @error_code VARCHAR(10),
        @normalized_param NVARCHAR(MAX) = @rule_params,
        @function_name SYSNAME,
        @function_sql NVARCHAR(300),
        @param_count INT,
        @sql NVARCHAR(MAX);

    IF @allow_null = 1 AND (@value IS NULL OR LTRIM(RTRIM(@value)) = '')
    BEGIN
        RETURN;
    END;

    IF @rule_code = 'ALPHA_ONLY'
        SET @is_valid = dbo.fn_IsAlphaOnly(@value);

    ELSE IF @rule_code = 'ALPHA_ONLY_NULL_OK'
        SET @is_valid = CASE WHEN @value IS NULL OR @value = '' THEN 1 ELSE dbo.fn_IsAlphaOnly(@value) END;

    ELSE IF @rule_code = 'DIGITS_ONLY'
        SET @is_valid = dbo.fn_IsDigitsOnly(@value);

    ELSE IF @rule_code = 'LEN_EQ'
    BEGIN
        DECLARE @len INT = TRY_CAST(JSON_VALUE(@rule_params, '$.len') AS INT);
        SET @is_valid = dbo.fn_HasExactLength(@value, @len);
    END

    ELSE IF @rule_code = 'DATE_VALID'
        SET @is_valid = dbo.fn_IsValidDate(@value);

    ELSE IF @rule_code = 'DATE_VALID_NULL_OK'
        SET @is_valid = CASE WHEN @value IS NULL OR @value = '' THEN 1 ELSE dbo.fn_IsValidDate(@value) END;

    ELSE IF @rule_code = 'AGE_RANGE'
    BEGIN
        DECLARE @minYears INT = TRY_CAST(JSON_VALUE(@rule_params, '$.min') AS INT);
        DECLARE @maxYears INT = TRY_CAST(JSON_VALUE(@rule_params, '$.max') AS INT);
        
        -- Try date-based legacy detection first, fallback to modern vf_age_range
        DECLARE @ageDate DATE = TRY_CONVERT(DATE, @value);
        IF @ageDate IS NOT NULL
            SET @is_valid = dbo.fn_IsAgeBetween(@ageDate, @minYears, @maxYears);
        ELSE
            SET @is_valid = dbo.vf_age_range(@value);
    END

    ELSE IF @rule_code = 'DATE_NOT_FUTURE'
        SET @is_valid = dbo.fn_IsNotFutureDate(TRY_CONVERT(DATE, @value));

    ELSE IF @rule_code = 'DATE_NOT_FUTURE_NULL_OK'
        SET @is_valid = CASE WHEN @value IS NULL OR @value = '' THEN 1 ELSE dbo.fn_IsNotFutureDate(TRY_CONVERT(DATE, @value)) END;

    ELSE IF @rule_code IN ('IN_LIST', 'IN_LIST_NULL_OK')
    BEGIN
        DECLARE @csv NVARCHAR(4000) = JSON_VALUE(@rule_params, '$.values');
        SET @is_valid =
            CASE
                WHEN @rule_code = 'IN_LIST_NULL_OK' AND (@value IS NULL OR @value = '') THEN 1
                ELSE dbo.fn_IsInList(@value, @csv)
            END;
    END

    ELSE IF @rule_code = 'NUM_RANGE'
    BEGIN
        DECLARE @min DECIMAL(18,4) = TRY_CAST(JSON_VALUE(@rule_params, '$.min') AS DECIMAL(18,4));
        DECLARE @max DECIMAL(18,4) = TRY_CAST(JSON_VALUE(@rule_params, '$.max') AS DECIMAL(18,4));
        SET @is_valid = dbo.fn_IsNumberInRange(TRY_CAST(@value AS DECIMAL(18,4)), @min, @max);
    END

    ELSE IF @rule_code = 'PAN_FORMAT'
        SET @is_valid = dbo.fn_IsValidPAN(@value);

    ELSE IF @rule_code = 'PHONE_START'
        SET @is_valid = dbo.fn_IsValidPhoneStart(@value);

    ELSE
    BEGIN
        IF @rule_params IS NOT NULL
        BEGIN
            IF @rule_code IN ('HasLength', 'exact_length', 'min_length', 'min_value', 'max_value')
               AND CHARINDEX('=', @rule_params) > 0
                SET @normalized_param = LTRIM(RTRIM(RIGHT(@rule_params, LEN(@rule_params) - CHARINDEX('=', @rule_params))));

            IF @rule_code IN ('is_in_list', 'gender_code')
               AND CHARINDEX('allowed=', @rule_params) > 0
                SET @normalized_param = LTRIM(RTRIM(SUBSTRING(@rule_params, LEN('allowed=') + 1, LEN(@rule_params))));
        END;

        SET @function_name = N'dbo.vf_' + @rule_code;

        IF OBJECT_ID(@function_name, 'FN') IS NOT NULL
        BEGIN
            SET @function_sql = N'dbo.' + QUOTENAME(N'vf_' + @rule_code);

            SELECT @param_count = COUNT(*)
            FROM sys.parameters
            WHERE object_id = OBJECT_ID(@function_name)
              AND parameter_id > 0;

            IF @param_count = 1
                SET @sql = N'SELECT @result = ' + @function_sql + N'(@value);';
            ELSE IF @param_count = 2
                SET @sql = N'SELECT @result = ' + @function_sql + N'(@value, @param);';
            ELSE IF @param_count = 3
                SET @sql = N'SELECT @result = ' + @function_sql + N'(@value, @comparison_value, @param);';

            IF @sql IS NOT NULL
            BEGIN
                EXEC sp_executesql
                    @sql,
                    N'@value NVARCHAR(4000), @comparison_value NVARCHAR(4000), @param NVARCHAR(MAX), @result BIT OUTPUT',
                    @value = @value,
                    @comparison_value = @comparison_value,
                    @param = @normalized_param,
                    @result = @is_valid OUTPUT;
            END
        END
    END

    IF @is_valid = 0
    BEGIN
        SET @error_code =
            COALESCE(
                @error_code_override,
                CASE @rule_code
                    WHEN 'ALPHA_ONLY' THEN 'E001'
                    WHEN 'ALPHA_ONLY_NULL_OK' THEN 'E001'
                    WHEN 'DIGITS_ONLY' THEN 'E002'
                    WHEN 'LEN_EQ' THEN 'E003'
                    WHEN 'DATE_VALID' THEN 'E004'
                    WHEN 'DATE_VALID_NULL_OK' THEN 'E004'
                    WHEN 'AGE_RANGE' THEN 'E005'
                    WHEN 'DATE_NOT_FUTURE' THEN 'E006'
                    WHEN 'DATE_NOT_FUTURE_NULL_OK' THEN 'E006'
                    WHEN 'IN_LIST' THEN 'E007'
                    WHEN 'IN_LIST_NULL_OK' THEN 'E007'
                    WHEN 'NUM_RANGE' THEN 'E008'
                    WHEN 'PAN_FORMAT' THEN 'E009'
                    WHEN 'PHONE_START' THEN 'E010'
                    ELSE 'E999'
                END
            );

        INSERT INTO dbo.error_log
            (table_name, record_identifier, failed_field, error_code, log_time)
        VALUES
            (@table_name, @record_id, @column_name, @error_code, SYSDATETIME());
    END
END;
