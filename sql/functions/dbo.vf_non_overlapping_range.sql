CREATE OR ALTER FUNCTION dbo.vf_non_overlapping_range
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    RETURN 0;
END
