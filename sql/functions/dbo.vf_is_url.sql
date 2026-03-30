CREATE OR ALTER FUNCTION dbo.vf_is_url
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; RETURN IIF((@value LIKE 'http://%' OR @value LIKE 'https://%') AND @value NOT LIKE '% %',1,0);
END
