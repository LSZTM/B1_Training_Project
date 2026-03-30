CREATE OR ALTER FUNCTION dbo.vf_gender_code
(
    @value NVARCHAR(MAX),
    @param NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; RETURN IIF(LTRIM(RTRIM(@value)) IN ('M','F','O','Male','Female','Other','Prefer not to say'),1,0);
END
