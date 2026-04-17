Sub CreateValidationPPT()
    Dim pptApp As Object
    Dim pptPres As Object
    Dim slideIndex As Integer
    Dim currentSlide As Object
    Dim titleShape As Object
    Dim contentShape As Object
    
    ' Initialize PowerPoint
    On Error Resume Next
    Set pptApp = GetObject(class:="PowerPoint.Application")
    If pptApp Is Nothing Then
        Set pptApp = CreateObject(class:="PowerPoint.Application")
    End If
    On Error GoTo 0
    
    Set pptPres = pptApp.Presentations.Add
    slideIndex = 1
    
    ' Title Slide
    Set currentSlide = pptPres.Slides.Add(slideIndex, 1) ' 1 = ppLayoutTitle
    currentSlide.Shapes(1).TextFrame.TextRange.Text = "DataGuard Validation Suite"
    currentSlide.Shapes(2).TextFrame.TextRange.Text = "Technical Overview of Existing Validation Functions" & vbCrLf & "Generated on " & Date
    slideIndex = slideIndex + 1
    
    ' Category Slides
    AddCategorySlide pptPres, slideIndex, "Format & Pattern Validations", _
        "vf_IsEmail, vf_IsURL, vf_IsIP_v4, vf_IsJSON, vf_IsUUID, vf_is_datetime, vf_IsDate", _
        "Validates standard string structures using SQL 'LIKE' patterns for complex formats or 'TRY_CAST' / 'ISDATE' for native type conversions."
        
    AddCategorySlide pptPres, slideIndex, "String Integrity & Sanitization", _
        "vf_trimmed, vf_no_emoji, vf_no_html_tags, vf_no_special_chars, vf_no_whitespace_only", _
        "Ensures data cleanliness by enforcing whitespace rules and excluding forbidden content (HTML, Emojis, Special Chars) via character matching."
        
    AddCategorySlide pptPres, slideIndex, "Numerical & Range Validations", _
        "vf_age_range, vf_min_value, vf_max_value, vf_percentage_range, vf_positive_only", _
        "Enforces boundary constraints on numeric data. Functions cast string inputs to numeric types and perform 'BETWEEN' or comparison checks."
        
    AddCategorySlide pptPres, slideIndex, "Data Integrity & Cross-Validation", _
        "vf_NOT_NULL, vf_is_unique, vf_foreign_key_check, vf_ColumnComparison", _
        "Manages relational integrity and uniqueness. Performs cross-column comparisons (e.g., StartDate < EndDate) or database lookups."
        
    AddCategorySlide pptPres, slideIndex, "Security & Privacy", _
        "vf_no_sql_injection, vf_no_pii_pattern, vf_no_cleartext_password, vf_masked_value", _
        "Protects against malicious data entry and data leaks. Scans for blacklisted keywords (EXEC, DROP) and identifies PII signatures like SSNs."
        
    AddCategorySlide pptPres, slideIndex, "Identity & Financial", _
        "vf_is_iban, vf_iban_checksum, vf_is_credit_card, vf_luhn_check, vf_is_ssn", _
        "Validates financial and identity tokens using industry-standard algorithms, such as the Luhn algorithm for cards and checksums for IBANs."
        
    AddCategorySlide pptPres, slideIndex, "Temporal & Holiday Logic", _
        "vf_date_not_in_future, vf_date_not_weekend, vf_date_not_holiday", _
        "Enforces business-day rules and scheduling constraints. Uses current date/time context and holiday definitions to validate entry."
        
    AddCategorySlide pptPres, slideIndex, "Geo-Spatial Validations", _
        "vf_is_latitude, vf_is_longitude", _
        "Verifies Geographic Coordinate System (GCS) bounds, ensuring Latitude is between -90/90 and Longitude is between -180/180."

    ' Show PowerPoint
    pptApp.Visible = True
    MsgBox "Presentation Generated successfully!", vbInformation
End Sub

Sub AddCategorySlide(pres As Object, ByRef idx As Integer, title As String, functions As String, logic As String)
    Dim sld As Object
    Set sld = pres.Slides.Add(idx, 2) ' 2 = ppLayoutText
    sld.Shapes(1).TextFrame.TextRange.Text = title
    sld.Shapes(2).TextFrame.TextRange.Text = "Example Functions:" & vbCrLf & functions & vbCrLf & vbCrLf & "How they work:" & vbCrLf & logic
    idx = idx + 1
End Sub
