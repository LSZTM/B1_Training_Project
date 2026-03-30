CREATE OR ALTER FUNCTION dbo.vf_is_base64
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; RETURN IIF(LEN(@value)%4=0 AND @value NOT LIKE '%[^A-Za-z0-9+/=]%',1,0);
END
