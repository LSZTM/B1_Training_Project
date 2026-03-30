CREATE OR ALTER FUNCTION dbo.vf_not_equal_to
(
    @value NVARCHAR(MAX),
    @param NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; RETURN IIF(@value<>@param,1,0);
END
