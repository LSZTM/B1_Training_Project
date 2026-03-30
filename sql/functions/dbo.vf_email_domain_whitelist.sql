CREATE OR ALTER FUNCTION dbo.vf_email_domain_whitelist
(
    @value NVARCHAR(MAX),
    @param NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; DECLARE @domain NVARCHAR(200)=LOWER(PARSENAME(REPLACE(@value,'@','.'),2)+'.'+PARSENAME(REPLACE(@value,'@','.'),1)); RETURN IIF(EXISTS(SELECT 1 FROM string_split(ISNULL(@param,''),',') s WHERE LOWER(LTRIM(RTRIM(s.value)))=@domain),1,0);
END
