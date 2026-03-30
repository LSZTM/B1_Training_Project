CREATE OR ALTER FUNCTION dbo.vf_masked_value
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; RETURN IIF(@value LIKE '%****%' OR @value LIKE '***%' OR @value LIKE '%xxx%' OR @value LIKE '%XXX%',1,0);
END
