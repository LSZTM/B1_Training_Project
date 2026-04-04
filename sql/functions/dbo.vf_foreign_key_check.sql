CREATE OR ALTER FUNCTION dbo.vf_foreign_key_check
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    RETURN 0;
END
