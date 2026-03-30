CREATE OR ALTER FUNCTION dbo.vf_exact_length
(
    @value NVARCHAR(MAX),
    @param NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; RETURN IIF(LEN(@value)=TRY_CAST(@param AS INT),1,0);
END
