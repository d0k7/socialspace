# update_handoff.ps1
$root        = "C:\Users\dheer\Downloads\socialspace-workspace\socialspace"
$handoffPath = "$root\docs\HANDOFF_CURRENT.md"
$quickPath   = "$root\docs\HANDOFF_QUICK.md"
$backupPath  = "$root\docs\HANDOFF_BACKUP.md"

if (-not (Test-Path $handoffPath)) {
    Write-Host "ERROR: HANDOFF_CURRENT.md not found at $handoffPath"
    exit 1
}

$claudeOutput = $null
try { $claudeOutput = Get-Clipboard -Format Text 2>$null } catch { }
if (-not $claudeOutput) {
    try { $claudeOutput = (Get-Clipboard) -join "`n" } catch { }
}
if (-not $claudeOutput -or $claudeOutput.Trim().Length -eq 0) {
    Write-Host "ERROR: Clipboard is empty. Copy Claude output first."
    exit 1
}
$lineCount = ($claudeOutput -split "`n").Count
Write-Host "Read $lineCount lines from clipboard."

Copy-Item $handoffPath $backupPath -Force
Write-Host "Backup saved: HANDOFF_BACKUP.md"

$handoff    = (Get-Content $handoffPath -Raw) -replace "`r`n", "`n"
$claudeNorm = $claudeOutput -replace "`r`n", "`n"

$sectionRx = [regex]'--- SECTION (\d+) UPDATED ---\n([\s\S]*?)--- END SECTION \1 ---'
$matches   = $sectionRx.Matches($claudeNorm)

$updatedSections = @()
$skippedSections = @()

foreach ($m in $matches) {
    $num        = $m.Groups[1].Value
    $newContent = $m.Groups[2].Value.Trim()
    $findRx     = [regex]("(?m)(### SECTION $num\b[^\n]*)\n([\s\S]*?)(?=### SECTION |\z)")
    if ($findRx.IsMatch($handoff)) {
        $safeContent = $newContent -replace '\\', '\\' -replace '\$', '$$$$'
        $replacement = '$1' + "`n$safeContent`n`n"
        $handoff = $findRx.Replace($handoff, $replacement)
        $updatedSections += $num
    } else {
        $skippedSections += $num
    }
}

$handoff = $handoff -replace "`n", "`r`n"
Set-Content $handoffPath $handoff -NoNewline -Encoding UTF8

$quickRx    = [regex]'--- HANDOFF_QUICK UPDATED ---\n([\s\S]*?)--- END HANDOFF_QUICK ---'
$quickMatch = $quickRx.Match($claudeNorm)
if ($quickMatch.Success) {
    $quickContent = $quickMatch.Groups[1].Value.Trim() -replace "`n", "`r`n"
    Set-Content $quickPath $quickContent -Encoding UTF8
    Write-Host "HANDOFF_QUICK.md updated."
} else {
    Write-Host "WARNING: No HANDOFF_QUICK block found."
}

Write-Host ""
if ($updatedSections.Count -gt 0) { Write-Host "Sections updated: $($updatedSections -join ', ')" }
if ($skippedSections.Count -gt 0) { Write-Host "Sections NOT found: $($skippedSections -join ', ')" }
if ($matches.Count -eq 0) { Write-Host "WARNING: No section blocks found in clipboard." }
Write-Host ""
Write-Host "Next: git add docs\HANDOFF_CURRENT.md docs\HANDOFF_QUICK.md"
