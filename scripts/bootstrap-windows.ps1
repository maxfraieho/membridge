# bootstrap-windows.ps1 — Deploy Claude config from membridge repo to %USERPROFILE%\.claude
# Does NOT touch: auth, tokens, credentials, plugins/cache, databases
#
# Usage: powershell -ExecutionPolicy Bypass -File scripts\bootstrap-windows.ps1

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoDir = Split-Path -Parent $ScriptDir
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupDir = Join-Path $ClaudeDir "backup\$Timestamp"
$ConfigSrc = Join-Path $RepoDir "config\claude"

Write-Host "=== Claude Config Bootstrap (Windows) ==="
Write-Host "Source:  $ConfigSrc"
Write-Host "Target:  $ClaudeDir"

# Verify source
if (-not (Test-Path $ConfigSrc)) {
    Write-Host "ERROR: Config source not found: $ConfigSrc" -ForegroundColor Red
    Write-Host "  Make sure you're running from the membridge repo."
    exit 1
}

# Create directories
New-Item -ItemType Directory -Force -Path $ClaudeDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $ClaudeDir "hooks") | Out-Null
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

# Backup existing safe files
Write-Host ""
Write-Host "--- Backing up existing config to $BackupDir ---"

foreach ($f in @("settings.json", "mcp.json")) {
    $src = Join-Path $ClaudeDir $f
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $BackupDir $f)
        Write-Host "  Backed up: $f"
    }
}

# Backup MCP configs
Get-ChildItem (Join-Path $ClaudeDir "mcp*.json") -ErrorAction SilentlyContinue | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $BackupDir $_.Name)
    Write-Host "  Backed up: $($_.Name)"
}

# Backup hooks
$hooksDir = Join-Path $ClaudeDir "hooks"
if ((Test-Path $hooksDir) -and (Get-ChildItem $hooksDir -ErrorAction SilentlyContinue)) {
    $backupHooks = Join-Path $BackupDir "hooks"
    New-Item -ItemType Directory -Force -Path $backupHooks | Out-Null
    Copy-Item (Join-Path $hooksDir "*") $backupHooks -Recurse
    Write-Host "  Backed up: hooks/"
}

# Deploy settings.json
Write-Host ""
Write-Host "--- Deploying config ---"

$settingsSrc = Join-Path $ConfigSrc "settings.json"
if (Test-Path $settingsSrc) {
    Copy-Item $settingsSrc (Join-Path $ClaudeDir "settings.json")
    Write-Host "  Deployed: settings.json"
}

# Deploy MCP configs
Get-ChildItem (Join-Path $ConfigSrc "mcp*.json") -ErrorAction SilentlyContinue | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $ClaudeDir $_.Name)
    Write-Host "  Deployed: $($_.Name)"
}

# Deploy hooks (as reference — bash hooks may not run natively on Windows)
$hooksSrc = Join-Path $ConfigSrc "hooks"
if (Test-Path $hooksSrc) {
    Get-ChildItem $hooksSrc -File -ErrorAction SilentlyContinue | ForEach-Object {
        Copy-Item $_.FullName (Join-Path $hooksDir $_.Name)
        Write-Host "  Deployed: hooks/$($_.Name) (reference only — may need WSL/Git Bash)"
    }
}

# Verify settings.json
Write-Host ""
Write-Host "--- Verification ---"
$settingsTarget = Join-Path $ClaudeDir "settings.json"
if (Test-Path $settingsTarget) {
    try {
        Get-Content $settingsTarget -Raw | ConvertFrom-Json | Out-Null
        Write-Host "  settings.json: valid JSON"
    } catch {
        Write-Host "  WARNING: settings.json is not valid JSON" -ForegroundColor Yellow
    }
}

# Safety check: no auth files in backup
foreach ($dangerous in @(".credentials.json", "auth", "token")) {
    if (Test-Path (Join-Path $BackupDir $dangerous)) {
        Write-Host "  ERROR: Auth file found in backup - this should not happen" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "=== SUCCESS ===" -ForegroundColor Green
Write-Host "Claude config deployed from membridge."
Write-Host "Auth/tokens remain untouched (local only)."
Write-Host "Backup: $BackupDir"
