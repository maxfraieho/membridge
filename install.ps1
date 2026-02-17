# Membridge Windows Installer
# Run: powershell -ExecutionPolicy Bypass -File install.ps1

param(
    [string]$Mode = "agent",
    [string]$InstallDir = "$env:USERPROFILE\membridge"
)

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/maxfraieho/membridge.git"

Write-Host "[membridge] Windows installer — mode=$Mode" -ForegroundColor Green
Write-Host "[membridge] Install directory: $InstallDir" -ForegroundColor Green

# --- Check Python ---
try {
    $pyVersion = & python --version 2>&1
    Write-Host "[membridge] $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "[membridge] Python not found. Install Python 3.11+ from python.org" -ForegroundColor Red
    exit 1
}

# --- Clone or update ---
if (Test-Path "$InstallDir\.git") {
    Write-Host "[membridge] Updating existing installation..." -ForegroundColor Green
    Push-Location $InstallDir
    git pull --ff-only 2>$null
    Pop-Location
} else {
    Write-Host "[membridge] Cloning membridge..." -ForegroundColor Green
    git clone $RepoUrl $InstallDir
}

Set-Location $InstallDir

# --- Create venv ---
if (-not (Test-Path ".venv")) {
    Write-Host "[membridge] Creating Python venv..." -ForegroundColor Green
    python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1

Write-Host "[membridge] Installing dependencies..." -ForegroundColor Green
pip install --quiet --upgrade pip
pip install --quiet fastapi uvicorn httpx pydantic boto3

# --- Generate env file ---
function New-RandomKey {
    $bytes = New-Object byte[] 24
    [Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($bytes)
    return ($bytes | ForEach-Object { $_.ToString("x2") }) -join ""
}

if ($Mode -eq "server" -or $Mode -eq "all") {
    if (-not (Test-Path ".env.server")) {
        $adminKey = New-RandomKey
        $agentKey = New-RandomKey
        @"
MEMBRIDGE_ADMIN_KEY=$adminKey
MEMBRIDGE_AGENT_KEY=$agentKey
MEMBRIDGE_DATA_DIR=$InstallDir\server\data
"@ | Set-Content -Path ".env.server"
        Write-Host "[membridge] Created .env.server with generated keys" -ForegroundColor Green
    }
}

if ($Mode -eq "agent" -or $Mode -eq "all") {
    if (-not (Test-Path ".env.agent")) {
        @"
MEMBRIDGE_AGENT_KEY=REPLACE_WITH_KEY_FROM_SERVER
MEMBRIDGE_AGENT_DRYRUN=0
MEMBRIDGE_HOOKS_BIN=$InstallDir\hooks
MEMBRIDGE_CONFIG_ENV=$env:USERPROFILE\.claude-mem-minio\config.env
"@ | Set-Content -Path ".env.agent"
        Write-Host "[membridge] Created .env.agent — edit MEMBRIDGE_AGENT_KEY" -ForegroundColor Yellow
    }
}

# --- Print instructions ---
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "[membridge] Installation complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if ($Mode -eq "server" -or $Mode -eq "all") {
    Write-Host "[membridge] Run server:" -ForegroundColor Green
    Write-Host "  cd $InstallDir" -ForegroundColor White
    Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  Get-Content .env.server | ForEach-Object { if (`$_ -match '(.+?)=(.+)') { [Environment]::SetEnvironmentVariable(`$matches[1], `$matches[2]) } }" -ForegroundColor White
    Write-Host "  python -m uvicorn server.main:app --host 0.0.0.0 --port 8000" -ForegroundColor White
    Write-Host ""
    Write-Host "[membridge] Or run as NSSM service:" -ForegroundColor Yellow
    Write-Host "  nssm install membridge-server $InstallDir\.venv\Scripts\python.exe -m uvicorn server.main:app --host 0.0.0.0 --port 8000" -ForegroundColor White
    Write-Host "  nssm set membridge-server AppDirectory $InstallDir" -ForegroundColor White
    Write-Host "  nssm set membridge-server AppEnvironmentExtra MEMBRIDGE_ADMIN_KEY=<key> MEMBRIDGE_AGENT_KEY=<key>" -ForegroundColor White
    Write-Host ""
}

if ($Mode -eq "agent" -or $Mode -eq "all") {
    Write-Host "[membridge] Run agent:" -ForegroundColor Green
    Write-Host "  cd $InstallDir" -ForegroundColor White
    Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  Get-Content .env.agent | ForEach-Object { if (`$_ -match '(.+?)=(.+)') { [Environment]::SetEnvironmentVariable(`$matches[1], `$matches[2]) } }" -ForegroundColor White
    Write-Host "  python -m uvicorn agent.main:app --host 0.0.0.0 --port 8001" -ForegroundColor White
    Write-Host ""
    Write-Host "[membridge] Or as scheduled task:" -ForegroundColor Yellow
    Write-Host "  schtasks /create /tn `"membridge-agent`" /tr `"$InstallDir\.venv\Scripts\python.exe -m uvicorn agent.main:app --host 0.0.0.0 --port 8001`" /sc onlogon" -ForegroundColor White
    Write-Host ""
}

Write-Host "[membridge] Healthcheck: curl http://localhost:8000/health (server) or :8001 (agent)" -ForegroundColor Green
