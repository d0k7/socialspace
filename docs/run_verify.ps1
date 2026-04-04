# run_verify.ps1
# PURPOSE: Run all project health checks and save output to VERIFICATION_OUTPUT.txt
#
# HOW TO RUN (from socialspace repo root in PowerShell):
#   .\docs\run_verify.ps1
#
# OUTPUT: docs\VERIFICATION_OUTPUT.txt
# Paste that file's contents into Claude when asked for verification.

$root   = "C:\Users\dheer\Downloads\socialspace-workspace\socialspace"
$output = "$root\docs\VERIFICATION_OUTPUT.txt"
$time   = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Add-Section($title, $content) {
    Add-Content -Path $output -Value "`r`n`r`n=== $title ==="
    Add-Content -Path $output -Value $content
}

# Check git is available
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "WARNING: git not found in PATH. Git section will be skipped."
    Write-Host "Install git from https://git-scm.com/download/win"
}

Set-Content -Path $output -Value "SOCIALSPACE VERIFICATION OUTPUT"
Add-Content -Path $output -Value "Generated: $time IST"
Add-Content -Path $output -Value "============================================"

# 1. GIT
Set-Location $root
Add-Section "GIT STATUS" (git status 2>&1 | Out-String)
Add-Section "GIT LOG (last 10)" (git log --oneline -10 2>&1 | Out-String)

# 2. BACKEND TESTS
$backendDir = "$root\backend"
if (Test-Path $backendDir) {
    Set-Location $backendDir
    Add-Section "BACKEND TESTS" (& "..\venv\Scripts\pytest.exe" tests -q 2>&1 | Out-String)
} else {
    Add-Section "BACKEND TESTS" "ERROR: backend directory not found at $backendDir"
}

# 3. FRONTEND BUILD
# Uses cmd /c to capture npm stderr correctly on Windows
# --no-color prevents ANSI escape codes polluting the output file
$frontendDir = "$root\frontend"
if (Test-Path $frontendDir) {
    Set-Location $frontendDir
    $buildRaw  = cmd /c "npm run build --no-color 2>&1"
    $buildTrim = ($buildRaw | Select-Object -First 150) -join "`n"
    Add-Section "FRONTEND BUILD (first 150 lines)" $buildTrim
} else {
    Add-Section "FRONTEND BUILD" "ERROR: frontend directory not found at $frontendDir"
}

# 4. TYPESCRIPT ERRORS (first 100 lines — errors repeat beyond that)
if (Test-Path $frontendDir) {
    Set-Location $frontendDir
    $tsRaw  = cmd /c "npx tsc --noEmit --pretty false 2>&1"
    $tsTrim = ($tsRaw | Select-Object -First 100) -join "`n"
    Add-Section "TYPESCRIPT ERRORS (first 100 lines)" $tsTrim
}

# 5. FILE STRUCTURE
# Properly excludes heavy folders by checking the full path string
Set-Location $root
$skipFolders = @("node_modules","venv","__pycache__",".git","dist","build",".vite",".next")
$files = Get-ChildItem -Recurse -File | Where-Object {
    $p    = $_.FullName
    $skip = $false
    foreach ($f in $skipFolders) {
        if ($p -like "*\$f\*") { $skip = $true; break }
    }
    -not $skip
} | Select-Object -ExpandProperty FullName

Add-Section "FILE STRUCTURE (heavy folders excluded)" ($files -join "`n")

# DONE
Add-Content -Path $output -Value "`r`n`r`n============================================"
Add-Content -Path $output -Value "END OF VERIFICATION OUTPUT"

$kb = [math]::Round((Get-Item $output).Length / 1KB, 1)
Write-Host ""
Write-Host "Done. Saved to: $output"
Write-Host "Size: $kb KB"
Write-Host ""

if ($kb -gt 200) {
    Write-Host "Output is large ($kb KB). Paste into Claude in this priority order:"
    Write-Host "  1. GIT STATUS + GIT LOG"
    Write-Host "  2. BACKEND TESTS"
    Write-Host "  3. TYPESCRIPT ERRORS"
    Write-Host "  4. FRONTEND BUILD"
    Write-Host "  5. FILE STRUCTURE (paste last or skip if still too long)"
} else {
    Write-Host "Safe to paste the entire file into Claude."
}
Write-Host ""
