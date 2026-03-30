CREATE OR ALTER FUNCTION dbo.vf_luhn_check
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; DECLARE @v NVARCHAR(MAX)=REPLACE(REPLACE(@value,' ',''),'-',''); IF @v LIKE '%[^0-9]%' RETURN 0; DECLARE @i INT=LEN(@v), @sum INT=0, @alt BIT=0, @d INT; WHILE @i>0 BEGIN SET @d=CONVERT(INT,SUBSTRING(@v,@i,1)); IF @alt=1 BEGIN SET @d=@d*2; IF @d>9 SET @d=@d-9; END; SET @sum=@sum+@d; SET @alt=IIF(@alt=1,0,1); SET @i=@i-1; END; RETURN IIF(@sum%10=0,1,0);
END
