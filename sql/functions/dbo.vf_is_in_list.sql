CREATE OR ALTER FUNCTION dbo.vf_is_in_list
(
    @value NVARCHAR(MAX),
    @param NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; RETURN IIF(EXISTS(SELECT 1 FROM string_split(ISNULL(@param,''),',') s WHERE LTRIM(RTRIM(s.value))=LTRIM(RTRIM(@value))),1,0);
END
