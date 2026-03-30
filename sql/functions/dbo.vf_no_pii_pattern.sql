CREATE OR ALTER FUNCTION dbo.vf_no_pii_pattern
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; DECLARE @u NVARCHAR(MAX)=@value; IF @u LIKE '%[0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9][0-9][0-9]%' RETURN 0; IF @u LIKE '%[0-9][0-9][0-9][0-9][ -][0-9][0-9][0-9][0-9][ -][0-9][0-9][0-9][0-9][ -][0-9][0-9][0-9][0-9]%' RETURN 0; IF @u LIKE '%_@_%.__%' RETURN 0; RETURN 1;
END
