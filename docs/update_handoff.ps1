# update_handoff.ps1
# VERSION: 3 (April 3 2026) — fixes regex $ corruption bug
#
# PURPOSE: Automatically updates HANDOFF_CURRENT.md and HANDOFF_QUICK.md
#          from Claude's session end output
#
# HOW TO USE:
#   1. At session end paste the session end template into Claude
#   2. Copy ALL of Claude's response (Ctrl+A then Ctrl+C in the chat)
#   3. Open PowerShell at repo root and run:
#        .\docs\update_handoff.ps1
#   Done. No file creation. Clipboard is read automatically.

$root        = "C:\Users\dheer\Downloads\socialspace-workspace\socialspace"
$handoffPath = "$root\docs\HANDOFF_CURRENT.md"
$quickPath   = "$root\docs\HANDOFF_QUICK.md"
$backupPath  = "$root\docs\HANDOFF_BACKUP.md"

# --- GUARD: handoff must exist ---
if (-not (Test-Path $handoffPath)) {
    Write-Host "ERROR: HANDOFF_CURRENT.md not found at $handoffPath"
    Write-Host "Save HANDOFF_CURRENT.md to that location first."
    exit 1
}

# --- READ FROM CLIPBOARD (PS5.1 and PS7 compatible) ---
$claudeOutput = $null
try   { $claudeOutput = Get-Clipboard -Format Text 2>$null } catch { }
if (-not $claudeOutput) {
    try { $claudeOutput = (Get-Clipboard) -join "`n" } catch { }
}
if (-not $claudeOutput -or $claudeOutput.Trim().Length -eq 0) {
    Write-Host "ERROR: Clipboard is empty."
    Write-Host "Copy ALL of Claude's session end response, then run this script again."
    Write-Host ""
    Write-Host "If clipboard never works on your machine, paste Claude's output into:"
    Write-Host "  $root\docs\SESSION_END_OUTPUT.txt"
    Write-Host "Then change line 33 of this script to:"
    Write-Host '  $claudeOutput = Get-Content "$root\docs\SESSION_END_OUTPUT.txt" -Raw'
    exit 1
}
$lineCount = ($claudeOutput -split "`n").Count
Write-Host "Read $lineCount lines from clipboard."

# --- BACKUP BEFORE TOUCHING ANYTHING ---
Copy-Item $handoffPath $backupPath -Force
Write-Host "Backup saved: HANDOFF_BACKUP.md"

# --- NORMALISE LINE ENDINGS ---
$handoff     = (Get-Content $handoffPath -Raw) -replace "`r`n", "`n"
$claudeNorm  = $claudeOutput               -replace "`r`n", "`n"

# --- EXTRACT SECTION UPDATES FROM CLAUDE OUTPUT ---
# Expected format:
#   --- SECTION N UPDATED ---
#   [content]
#   --- END SECTION N ---
$sectionRx = [regex]'--- SECTION (\d+) UPDATED ---\n([\s\S]*?)--- END SECTION \1 ---'
$matches   = $sectionRx.Matches($claudeNorm)

$updatedSections = @()
$skippedSections = @()

foreach ($m in $matches) {
    $num        = $m.Groups[1].Value
    $newContent = $m.Groups[2].Value.Trim()

    # Find the section in the handoff.
    # Capture group 1 = the full original header line (preserves title).
    # Section ends just before the next ### SECTION header or end of file.
    $findRx = [regex]("(?m)(### SECTION $num\b[^\n]*)\n([\s\S]*?)(?=### SECTION |\z)")

    if ($findRx.IsMatch($handoff)) {

        # CRITICAL: .NET Replace() treats $ in replacement as backreference.
        # We must escape ALL $ in newContent so they survive as literal $.
        # Also escape \ because it is the other special char in replacements.
        $safeContent = $newContent -replace '\\', '\\' -replace '\$', '$$$$'

        # $1 here is a .NET backreference to capture group 1 = original header line.
        $replacement = '$1' + "`n$safeContent`n`n"

        $handoff = $findRx.Replace($handoff, $replacement)
        $updatedSections += $num
    } else {
        $skippedSections += $num
    }
}

# --- SAVE UPDATED HANDOFF (restore CRLF for Windows) ---
$handoff = $handoff -replace "`n", "`r`n"
Set-Content $handoffPath $handoff -NoNewline -Encoding UTF8

# --- EXTRACT AND SAVE HANDOFF_QUICK ---
$quickRx    = [regex]'--- HANDOFF_QUICK UPDATED ---\n([\s\S]*?)--- END HANDOFF_QUICK ---'
$quickMatch = $quickRx.Match($claudeNorm)

if ($quickMatch.Success) {
    $quickContent = $quickMatch.Groups[1].Value.Trim() -replace "`n", "`r`n"
    Set-Content $quickPath $quickContent -Encoding UTF8
    Write-Host "HANDOFF_QUICK.md updated."
} else {
    Write-Host "WARNING: No HANDOFF_QUICK block found in Claude's output."
    Write-Host "  Make sure the session end template asks for HANDOFF_QUICK UPDATED."
}

# --- REPORT ---
Write-Host ""
if ($updatedSections.Count -gt 0) {
    Write-Host "Sections updated  : $($updatedSections -join ', ')"
}
if ($skippedSections.Count -gt 0) {
    Write-Host "Sections NOT found: $($skippedSections -join ', ')"
    Write-Host "  Check that HANDOFF_CURRENT.md uses  ### SECTION N  headers."
}
if ($matches.Count -eq 0) {
    Write-Host "WARNING: No section blocks found in clipboard output."
    Write-Host "  Claude must use the exact format:"
    Write-Host "    --- SECTION N UPDATED ---"
    Write-Host "    [content]"
    Write-Host "    --- END SECTION N ---"
}

# --- REMIND TO COMMIT ---
Write-Host ""
Write-Host "Next step — commit to git:"
Write-Host "  git add docs\HANDOFF_CURRENT.md docs\HANDOFF_QUICK.md"
$today = Get-Date -Format 'yyyy-MM-dd'
Write-Host "  git commit -m `"handoff: $today session update`""
