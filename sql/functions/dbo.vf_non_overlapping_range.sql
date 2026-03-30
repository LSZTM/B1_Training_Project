CREATE OR ALTER FUNCTION dbo.vf_non_overlapping_range
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; RETURN 1;
END
