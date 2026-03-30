CREATE OR ALTER FUNCTION dbo.vf_IsEmail
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; RETURN IIF(@value LIKE '%_@_%.__%' AND @value NOT LIKE '% %' AND @value NOT LIKE '%@@%' AND LEN(@value)<=254,1,0);
END
