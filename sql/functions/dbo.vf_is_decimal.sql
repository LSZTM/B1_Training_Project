CREATE OR ALTER FUNCTION dbo.vf_is_decimal
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; IF @value LIKE '%[$,]%' RETURN 0; IF LEN(@value)-LEN(REPLACE(@value,'.',''))>1 RETURN 0; RETURN IIF(ISNUMERIC(@value)=1,1,0);
END
