CREATE OR ALTER FUNCTION dbo.vf_no_sql_injection
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; DECLARE @u NVARCHAR(MAX)=UPPER(@value); RETURN IIF(@u LIKE '%--%' OR @u LIKE '% XP_%' OR @u LIKE '%EXEC%' OR @u LIKE '%DROP %' OR @u LIKE '%UNION %' OR @u LIKE '%;%' OR @u LIKE '%/*%' OR @u LIKE '%*/%',0,1);
END
