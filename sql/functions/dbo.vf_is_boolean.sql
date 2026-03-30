CREATE OR ALTER FUNCTION dbo.vf_is_boolean
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; DECLARE @v NVARCHAR(20)=LOWER(LTRIM(RTRIM(@value))); RETURN IIF(@v IN ('0','1','true','false','yes','no','t','f'),1,0);
END
