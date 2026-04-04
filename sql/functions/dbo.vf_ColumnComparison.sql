CREATE OR ALTER FUNCTION dbo.vf_ColumnComparison
(
    @left_value NVARCHAR(MAX),
    @right_value NVARCHAR(MAX),
    @param NVARCHAR(MAX) = NULL
)
RETURNS BIT
AS
BEGIN
    IF @left_value IS NULL OR @right_value IS NULL RETURN 1;

    DECLARE @operator NVARCHAR(4) = '=';
    IF @param IS NOT NULL AND CHARINDEX('operator=', @param) > 0
    BEGIN
        DECLARE @start INT = CHARINDEX('operator=', @param) + LEN('operator=');
        DECLARE @end INT = CHARINDEX(',', @param + ',', @start);
        SET @operator = LTRIM(RTRIM(SUBSTRING(@param, @start, @end - @start)));
    END

    RETURN IIF(
        (@operator = '>'  AND TRY_CONVERT(SQL_VARIANT, @left_value) >  TRY_CONVERT(SQL_VARIANT, @right_value)) OR
        (@operator = '<'  AND TRY_CONVERT(SQL_VARIANT, @left_value) <  TRY_CONVERT(SQL_VARIANT, @right_value)) OR
        (@operator = '>=' AND TRY_CONVERT(SQL_VARIANT, @left_value) >= TRY_CONVERT(SQL_VARIANT, @right_value)) OR
        (@operator = '<=' AND TRY_CONVERT(SQL_VARIANT, @left_value) <= TRY_CONVERT(SQL_VARIANT, @right_value)) OR
        (@operator = '!=' AND ISNULL(@left_value, '') <> ISNULL(@right_value, '')) OR
        (@operator = '='  AND ISNULL(@left_value, '') = ISNULL(@right_value, '')),
        1, 0
    );
END
