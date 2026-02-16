# bootstrap-windows.ps1 — Deploy Claude config via WSL2 + native Windows config
# Strategy: MinIO sync runs through WSL2; config files also deployed to Windows-native ~/.claude
# Does NOT touch: auth, tokens, credentials, plugins/cache, databases
#
# Usage: powershell -ExecutionPolicy Bypass -File scripts\bootstrap-windows.ps1

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoDir = Split-Path -Parent $ScriptDir
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"
$ClaudeHomeSrc = Join-Path $RepoDir "claude-home"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupDir = Join-Path $ClaudeDir "backup\$Timestamp"

Write-Host "=== Membridge Bootstrap (Windows + WSL2) ==="
Write-Host "Source:  $ClaudeHomeSrc"
Write-Host "Target:  $ClaudeDir"
Write-Host ""

# --- 1. Check WSL2 is available ---
Write-Host "--- Checking WSL2 ---"

$wslAvailable = $false
try {
    $wslStatus = wsl --status 2>&1
    if ($LASTEXITCODE -eq 0) {
        $wslAvailable = $true
        Write-Host "  OK: WSL2 is available"
    }
} catch {
    # wsl command not found
}

if (-not $wslAvailable) {
    # Try listing distros as fallback
    try {
        $distros = wsl --list --quiet 2>&1
        if ($distros -and $distros.Length -gt 0) {
            $wslAvailable = $true
            Write-Host "  OK: WSL2 distros found"
        }
    } catch {}
}

if (-not $wslAvailable) {
    Write-Host "  WARNING: WSL2 not detected. MinIO sync will not work." -ForegroundColor Yellow
    Write-Host "  Install WSL2: wsl --install"
    Write-Host "  Continuing with Windows-native config deploy only..."
    Write-Host ""
}

# --- 2. Clone/update membridge inside WSL2 ---
if ($wslAvailable) {
    Write-Host ""
    Write-Host "--- Setting up membridge in WSL2 ---"

    # Check if repo exists in WSL2
    $wslRepoExists = wsl bash -lc "test -d ~/membridge/.git && echo yes || echo no" 2>&1
    if ($wslRepoExists.Trim() -eq "yes") {
        Write-Host "  Updating existing repo in WSL2..."
        wsl bash -lc "cd ~/membridge && git pull --ff-only" 2>&1 | ForEach-Object { Write-Host "  $_" }
    } else {
        Write-Host "  Cloning membridge into WSL2..."
        wsl bash -lc "git clone git@github.com:maxfraieho/membridge.git ~/membridge" 2>&1 | ForEach-Object { Write-Host "  $_" }
    }

    # --- 3. Run bootstrap-linux.sh inside WSL2 ---
    Write-Host ""
    Write-Host "--- Running Linux bootstrap inside WSL2 ---"
    wsl bash -lc "cd ~/membridge && bash scripts/bootstrap-linux.sh" 2>&1 | ForEach-Object { Write-Host "  $_" }

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  WARNING: WSL2 bootstrap returned non-zero exit code" -ForegroundColor Yellow
    } else {
        Write-Host "  OK: WSL2 bootstrap completed"
    }
}

# --- 4. Deploy config to Windows-native ~/.claude ---
Write-Host ""
Write-Host "--- Deploying to Windows-native $ClaudeDir ---"

# Verify source
if (-not (Test-Path $ClaudeHomeSrc)) {
    Write-Host "ERROR: Source not found: $ClaudeHomeSrc" -ForegroundColor Red
    Write-Host "  Make sure you're running from the membridge repo."
    exit 1
}

# Create directories
New-Item -ItemType Directory -Force -Path $ClaudeDir | Out-Null
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

# Backup existing safe files
Write-Host ""
Write-Host "--- Backing up existing config to $BackupDir ---"

foreach ($f in @("CLAUDE.md", "settings.json", "mcp.json")) {
    $src = Join-Path $ClaudeDir $f
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $BackupDir $f)
        Write-Host "  Backed up: $f"
    }
}

# Backup directories
foreach ($d in @("skills", "skills-local", "skills-installer", "hooks", "commands")) {
    $srcDir = Join-Path $ClaudeDir $d
    if (Test-Path $srcDir) {
        $destDir = Join-Path $BackupDir $d
        Copy-Item $srcDir $destDir -Recurse
        Write-Host "  Backed up: $d/"
    }
}

# Deploy from claude-home/
Write-Host ""
Write-Host "--- Deploying claude-home/ ---"

# Deploy CLAUDE.md
$claudeMdSrc = Join-Path $ClaudeHomeSrc "CLAUDE.md"
if (Test-Path $claudeMdSrc) {
    Copy-Item $claudeMdSrc (Join-Path $ClaudeDir "CLAUDE.md")
    Write-Host "  Deployed: CLAUDE.md"
}

# Deploy directories (these work natively in Claude for Windows)
foreach ($d in @("skills", "skills-local", "skills-installer", "hooks", "commands")) {
    $srcDir = Join-Path $ClaudeHomeSrc $d
    if (Test-Path $srcDir) {
        $destDir = Join-Path $ClaudeDir $d
        if (Test-Path $destDir) { Remove-Item $destDir -Recurse -Force }
        Copy-Item $srcDir $destDir -Recurse
        Write-Host "  Deployed: $d/"
    }
}

# Deploy plugins metadata only (NOT cache)
$pluginsSrc = Join-Path $ClaudeHomeSrc "plugins"
if (Test-Path $pluginsSrc) {
    $pluginsDest = Join-Path $ClaudeDir "plugins"
    New-Item -ItemType Directory -Force -Path $pluginsDest | Out-Null
    foreach ($f in @("installed_plugins.json", "known_marketplaces.json", "CLAUDE.md")) {
        $pSrc = Join-Path $pluginsSrc $f
        if (Test-Path $pSrc) {
            Copy-Item $pSrc (Join-Path $pluginsDest $f)
            Write-Host "  Deployed: plugins/$f"
        }
    }
}

# Deploy settings.json from claude-home/ (if present)
$settingsSrc = Join-Path $ClaudeHomeSrc "settings.json"
if (Test-Path $settingsSrc) {
    Copy-Item $settingsSrc (Join-Path $ClaudeDir "settings.json")
    Write-Host "  Deployed: settings.json (from claude-home/)"
}

# --- 5. Create convenience .cmd scripts for WSL2 sync ---
if ($wslAvailable) {
    Write-Host ""
    Write-Host "--- Creating convenience scripts ---"

    $binDir = Join-Path $RepoDir "bin"
    New-Item -ItemType Directory -Force -Path $binDir | Out-Null

    # cm-push.cmd
    $pushCmd = Join-Path $binDir "cm-push.cmd"
    @"
@echo off
wsl bash -lc "~/.claude-mem-minio/bin/claude-mem-push"
"@ | Set-Content $pushCmd
    Write-Host "  Created: bin/cm-push.cmd"

    # cm-pull.cmd
    $pullCmd = Join-Path $binDir "cm-pull.cmd"
    @"
@echo off
wsl bash -lc "~/.claude-mem-minio/bin/claude-mem-pull"
"@ | Set-Content $pullCmd
    Write-Host "  Created: bin/cm-pull.cmd"

    # cm-doctor.cmd
    $doctorCmd = Join-Path $binDir "cm-doctor.cmd"
    @"
@echo off
wsl bash -lc "~/.claude-mem-minio/bin/claude-mem-doctor"
"@ | Set-Content $doctorCmd
    Write-Host "  Created: bin/cm-doctor.cmd"

    # cm-status.cmd
    $statusCmd = Join-Path $binDir "cm-status.cmd"
    @"
@echo off
wsl bash -lc "~/.claude-mem-minio/bin/claude-mem-status"
"@ | Set-Content $statusCmd
    Write-Host "  Created: bin/cm-status.cmd"
}

# --- 6. Verification ---
Write-Host ""
Write-Host "--- Verification ---"

$errors = 0

# Check settings.json valid JSON
$settingsTarget = Join-Path $ClaudeDir "settings.json"
if (Test-Path $settingsTarget) {
    try {
        Get-Content $settingsTarget -Raw | ConvertFrom-Json | Out-Null
        Write-Host "  OK: settings.json is valid JSON"
    } catch {
        Write-Host "  WARNING: settings.json is not valid JSON" -ForegroundColor Yellow
        $errors++
    }
}

# Check skills present
$skillsDir = Join-Path $ClaudeDir "skills"
if ((Test-Path $skillsDir) -and (Get-ChildItem $skillsDir -Directory -ErrorAction SilentlyContinue)) {
    $skillCount = (Get-ChildItem $skillsDir -Directory).Count
    Write-Host "  OK: skills/ present ($skillCount skills)"
} else {
    Write-Host "  WARNING: skills/ empty or missing" -ForegroundColor Yellow
    $errors++
}

# Check hooks present
$hooksDir = Join-Path $ClaudeDir "hooks"
if ((Test-Path $hooksDir) -and (Get-ChildItem $hooksDir -ErrorAction SilentlyContinue)) {
    Write-Host "  OK: hooks/ present"
} else {
    Write-Host "  WARNING: hooks/ empty or missing" -ForegroundColor Yellow
    $errors++
}

# Safety check: no auth files in backup
foreach ($dangerous in @(".credentials.json", "auth.json")) {
    if (Test-Path (Join-Path $BackupDir $dangerous)) {
        Write-Host "  ERROR: Auth file found in backup - this should not happen" -ForegroundColor Red
        $errors++
    }
}

# --- Summary ---
Write-Host ""
if ($errors -eq 0) {
    Write-Host "=== SUCCESS ===" -ForegroundColor Green
} else {
    Write-Host "=== COMPLETED WITH $errors WARNING(S) ===" -ForegroundColor Yellow
}
Write-Host "Windows-native Claude config deployed from claude-home/"
if ($wslAvailable) {
    Write-Host "WSL2 MinIO sync deployed (use cm-push.cmd / cm-pull.cmd)"
} else {
    Write-Host "WSL2 not available — install WSL2 for MinIO sync support"
}
Write-Host "Auth/tokens remain untouched (local only)"
Write-Host "Backup: $BackupDir"
Write-Host ""
Write-Host "--- Next steps ---"
if ($wslAvailable) {
    Write-Host "1. Edit MinIO credentials (in WSL2): wsl nano ~/.claude-mem-minio/config.env"
    Write-Host "2. Run diagnostics:                  bin\cm-doctor.cmd"
    Write-Host "3. First sync:                       bin\cm-pull.cmd"
} else {
    Write-Host "1. Install WSL2:  wsl --install"
    Write-Host "2. Re-run this script after WSL2 is ready"
}
