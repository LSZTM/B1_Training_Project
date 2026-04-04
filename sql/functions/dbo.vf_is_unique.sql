CREATE OR ALTER FUNCTION dbo.vf_is_unique
(
    @duplicate_rows INT,
    @rows_scanned INT
)
RETURNS BIT
AS
BEGIN
    IF ISNULL(@rows_scanned, 0) = 0 RETURN 1;
    RETURN IIF(ISNULL(@duplicate_rows, 0) = 0, 1, 0);
END
