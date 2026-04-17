Sub CreateRuleSuggestionDeepDive()
    Dim pptApp As Object
    Dim pptPres As Object
    Dim slideIndex As Integer
    Dim currentSlide As Object
    
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
    Set currentSlide = pptPres.Slides.Add(slideIndex, 1) ' ppLayoutTitle
    currentSlide.Shapes(1).TextFrame.TextRange.Text = "Rule Suggestion System"
    currentSlide.Shapes(2).TextFrame.TextRange.Text = "Deep Dive: The Multi-Pass Inference Engine" & vbCrLf & "Generated on " & Date
    slideIndex = slideIndex + 1
    
    ' Overview Slide
    AddDeepDiveSlide pptPres, slideIndex, "System Architecture Overview", _
        "Objective: Minimize manual effort in ruleset definition." & vbCrLf & _
        "Approach: Multi-pass statistical and semantic profiling." & vbCrLf & _
        "Sample Size: Configurable (Default 150-200 rows) for optimal speed vs. accuracy."
        
    ' Stage 1
    AddDeepDiveSlide pptPres, slideIndex, "Phase 1: Context & Sampling", _
        "1. Schema Retrieval: Fetches Data Type, Precision, and Max Length from INFORMATION_SCHEMA." & vbCrLf & _
        "2. Null Rate Calculation: SUM(CASE WHEN IS NULL)/COUNT to determine column sparsity." & vbCrLf & _
        "3. Smart Sampling: Fetches TOP(N) non-null values for content analysis."
        
    ' Stage 2
    AddDeepDiveSlide pptPres, slideIndex, "Phase 2: Semantic Keyword Analysis", _
        "Logic: Scans column names for domain-specific keywords defined in RULE_SIGNAL_MAP." & vbCrLf & _
        "- Key 'qty' or 'count' -> suggests 'is_digit'" & vbCrLf & _
        "- Key 'amount' or 'price' -> suggests 'is_decimal'" & vbCrLf & _
        "- Key 'email' -> suggests 'IsEmail'"
        
    ' Stage 3
    AddDeepDiveSlide pptPres, slideIndex, "Phase 3: Statistical Inference", _
        "Logic: Analyzes distribution of sampled numeric data." & vbCrLf & _
        "- Percentile Bounds: Inferred 'min_value' (p05) and 'max_value' (p95)." & vbCrLf & _
        "- Domain Checks: Detects if values are 100% positive or within [0-100] percentage range." & vbCrLf & _
        "- Date Bounds: Inferred 'date_not_in_future' and epoch checks."
        
    ' Stage 4
    AddDeepDiveSlide pptPres, slideIndex, "Phase 4: Pattern & Cardinality", _
        "- Regex Detectors: Matches strings against 20+ preset patterns (SSN, IP, UUID, JSON)." & vbCrLf & _
        "- Cardinality: If unique values <= 15, suggests 'is_in_list' with enumerated values." & vbCrLf & _
        "- Identity Check: High uniqueness + 'ID/Code' keywords -> suggests 'is_unique'."
        
    ' Stage 5
    AddDeepDiveSlide pptPres, slideIndex, "Phase 5: Agreement Scoring", _
        "Confidence is boosted if multiple signals align:" & vbCrLf & _
        "- SIGNAL BOOST: If (Keyword Signal) AND (Data Pattern Match) -> Confidence++." & vbCrLf & _
        "- CONFLICT DROP: If (Keyword Signal) AND NOT (Data Matching) -> Suggestion discarded." & vbCrLf & _
        "Ensures high-fidelity recommendations."
        
    ' Stage 6
    AddDeepDiveSlide pptPres, slideIndex, "Phase 6: Hygiene & Security Fallbacks", _
        "When data is 'Sparse' or 'Opaque', the system fails over to safety rules:" & vbCrLf & _
        "- Security: 'no_sql_injection', 'no_pii_pattern', 'no_html_tags'." & vbCrLf & _
        "- Hygiene: 'trimmed', 'encoding_check', 'no_whitespace_only'."
        
    ' Conclusion
    AddDeepDiveSlide pptPres, slideIndex, "Outcome: Smart Rule Addition", _
        "Final Output: A sorted list of recommendations with:" & vbCrLf & _
        "- Confidence Score (0.0 - 1.0)" & vbCrLf & _
        "- Human-readable Rationale (Why this rule was suggested)" & vbCrLf & _
        "- Suggested Parameters (min, max, allowed lists)"

    ' Show PowerPoint
    pptApp.Visible = True
    MsgBox "Rule Suggestion Deep Dive PPT Generated!", vbInformation
End Sub

Sub AddDeepDiveSlide(pres As Object, ByRef idx As Integer, title As String, content As String)
    Dim sld As Object
    Set sld = pres.Slides.Add(idx, 2) ' ppLayoutText
    sld.Shapes(1).TextFrame.TextRange.Text = title
    sld.Shapes(2).TextFrame.TextRange.Text = content
    idx = idx + 1
End Sub
