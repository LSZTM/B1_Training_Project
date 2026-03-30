CREATE OR ALTER FUNCTION dbo.vf_is_ip_v4
(
    @value NVARCHAR(MAX)
)
RETURNS BIT
AS
BEGIN
    IF @value IS NULL RETURN 1; DECLARE @xml XML=TRY_CAST('<x><i>'+REPLACE(@value,'.','</i><i>')+'</i></x>' AS XML); IF @xml IS NULL RETURN 0; IF @xml.value('count(/x/i)','int')<>4 RETURN 0; IF EXISTS(SELECT 1 FROM (SELECT T.N.value('.','nvarchar(10)') AS oct FROM @xml.nodes('/x/i') AS T(N)) s WHERE TRY_CONVERT(int,oct) IS NULL OR TRY_CONVERT(int,oct) NOT BETWEEN 0 AND 255) RETURN 0; RETURN 1;
END
