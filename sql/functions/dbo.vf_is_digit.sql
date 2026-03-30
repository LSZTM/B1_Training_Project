CREATE OR ALTER FUNCTION dbo.vf_is_digit
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; RETURN IIF(@value NOT LIKE '%[^0-9]%' AND LEN(@value)>0,1,0);
END
