CREATE OR ALTER FUNCTION dbo.vf_no_trailing_whitespace
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; RETURN IIF(@value=RTRIM(@value),1,0);
END
