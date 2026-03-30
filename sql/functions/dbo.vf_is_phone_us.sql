CREATE OR ALTER FUNCTION dbo.vf_is_phone_us
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; DECLARE @v NVARCHAR(MAX)=REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(@value,' ',''),'-',''),'(',''),')',''),'.',''); RETURN IIF(LEN(@v)=10 AND @v NOT LIKE '%[^0-9]%',1,0);
END
