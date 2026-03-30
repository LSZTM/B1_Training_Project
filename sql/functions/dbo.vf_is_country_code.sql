CREATE OR ALTER FUNCTION dbo.vf_is_country_code
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; RETURN IIF(LEN(@value)=2 AND @value NOT LIKE '%[^A-Za-z]%',1,0);
END
