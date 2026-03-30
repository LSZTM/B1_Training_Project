CREATE OR ALTER FUNCTION dbo.vf_no_special_chars
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; RETURN IIF(@value LIKE '%[^A-Za-z0-9 _.-]%',0,1);
END
