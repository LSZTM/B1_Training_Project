CREATE OR ALTER FUNCTION dbo.vf_case_consistency
(
    @value NVARCHAR(MAX),
    @param NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; DECLARE @e NVARCHAR(20)=LOWER(ISNULL(@param,'upper')); IF @e='upper' RETURN IIF(@value=UPPER(@value),1,0); IF @e='lower' RETURN IIF(@value=LOWER(@value),1,0); RETURN IIF(@value IN (UPPER(@value),LOWER(@value)),1,0);
END
