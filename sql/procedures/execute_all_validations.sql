SET QUOTED_IDENTIFIER ON;
SET ANSI_NULLS ON;
GO

CREATE OR ALTER PROCEDURE dbo.execute_all_validations
    @table_names_csv NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @t NVARCHAR(128), @c NVARCHAR(128), @r NVARCHAR(64), @p NVARCHAR(MAX);
    DECLARE @filter TABLE (name NVARCHAR(128));

    IF @table_names_csv IS NOT NULL
        INSERT INTO @filter SELECT LTRIM(RTRIM(value)) FROM STRING_SPLIT(@table_names_csv, ',');

    DECLARE config_cursor CURSOR LOCAL FAST_FORWARD FOR
        SELECT table_name, column_name, rule_code, NULLIF(rule_params, '')
        FROM dbo.temp_validation_config
        WHERE is_active = 1
          AND (@table_names_csv IS NULL OR table_name IN (SELECT name FROM @filter));

    OPEN config_cursor;
    FETCH NEXT FROM config_cursor INTO @t, @c, @r, @p;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        EXEC dbo.vp_validate_column @t, @c, @r, @p;
        FETCH NEXT FROM config_cursor INTO @t, @c, @r, @p;
    END;

    CLOSE config_cursor;
    DEALLOCATE config_cursor;
END;
GO
