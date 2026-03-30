CREATE OR ALTER FUNCTION dbo.vf_is_postal_code_uk
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; DECLARE @v NVARCHAR(16)=UPPER(LTRIM(RTRIM(@value))); RETURN IIF(@v LIKE '[A-Z][0-9] [0-9][A-Z][A-Z]' OR @v LIKE '[A-Z][A-Z][0-9] [0-9][A-Z][A-Z]' OR @v LIKE '[A-Z][0-9][A-Z] [0-9][A-Z][A-Z]' OR @v LIKE '[A-Z][A-Z][0-9][A-Z] [0-9][A-Z][A-Z]',1,0);
END
