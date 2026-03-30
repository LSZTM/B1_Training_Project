CREATE OR ALTER FUNCTION dbo.vf_is_ip_v6
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; RETURN IIF(@value LIKE '%:%' AND @value NOT LIKE '%[^0-9A-Fa-f:]%',1,0);
END
