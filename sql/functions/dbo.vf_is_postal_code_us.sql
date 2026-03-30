CREATE OR ALTER FUNCTION dbo.vf_is_postal_code_us
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; RETURN IIF(@value LIKE '[0-9][0-9][0-9][0-9][0-9]' OR @value LIKE '[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]',1,0);
END
