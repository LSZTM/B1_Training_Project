CREATE OR ALTER FUNCTION dbo.vf_iban_checksum
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; DECLARE @iban NVARCHAR(64)=UPPER(REPLACE(@value,' ','')); IF LEN(@iban)<5 OR @iban LIKE '%[^A-Z0-9]%' RETURN 0; SET @iban = SUBSTRING(@iban,5,LEN(@iban)-4)+LEFT(@iban,4); DECLARE @expanded NVARCHAR(MAX)='', @i INT=1, @c NCHAR(1); WHILE @i<=LEN(@iban) BEGIN SET @c=SUBSTRING(@iban,@i,1); SET @expanded=@expanded + CASE WHEN @c BETWEEN 'A' AND 'Z' THEN CAST(ASCII(@c)-55 AS NVARCHAR(2)) ELSE @c END; SET @i=@i+1; END; DECLARE @rem BIGINT=0,@chunk NVARCHAR(9); SET @i=1; WHILE @i<=LEN(@expanded) BEGIN SET @chunk=CAST(@rem AS NVARCHAR(20))+SUBSTRING(@expanded,@i,9); SET @rem=CAST(@chunk AS BIGINT)%97; SET @i=@i+9; END; RETURN IIF(@rem=1,1,0);
END
