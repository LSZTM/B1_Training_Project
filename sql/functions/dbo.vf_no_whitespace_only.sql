CREATE OR ALTER FUNCTION dbo.vf_no_whitespace_only
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; RETURN IIF(LTRIM(RTRIM(@value))<>'',1,0);
END
