CREATE OR ALTER FUNCTION dbo.vf_is_integer_string
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; DECLARE @v NVARCHAR(MAX)=LTRIM(RTRIM(@value)); IF LEFT(@v,1)='-' SET @v=SUBSTRING(@v,2,LEN(@v)); RETURN IIF(@v<>'' AND @v NOT LIKE '%[^0-9]%',1,0);
END
