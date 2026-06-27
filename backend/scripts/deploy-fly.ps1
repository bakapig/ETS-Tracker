#Requires -Version 5.1
<#
.SYNOPSIS
  Deploy KTMB Live API to Fly.io (Singapore region).

.PARAMETER FirstTime
  Run fly launch, create secrets, then deploy.

.PARAMETER SkipSecrets
  Do not prompt to set API_KEY / ADMIN_API_KEY.

.EXAMPLE
  cd backend
  .\scripts\deploy-fly.ps1 -FirstTime
#>
param(
    [switch]$FirstTime,
    [switch]$SkipSecrets
)

$ErrorActionPreference = "Stop"
$BackendRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $BackendRoot

function Get-FlyCmd {
    if (Get-Command fly -ErrorAction SilentlyContinue) { return "fly" }
    $local = Join-Path $env:USERPROFILE ".fly\bin\fly.exe"
    if (Test-Path $local) { return $local }
    return $null
}

function Install-Flyctl {
    Write-Host "Installing flyctl to $env:USERPROFILE\.fly\bin ..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri "https://fly.io/install.ps1" -UseBasicParsing | Invoke-Expression
}

function New-RandomKey {
    param([int]$Length = 32)
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    -join ((1..$Length) | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
}

$fly = Get-FlyCmd
if (-not $fly) {
    Install-Flyctl
    $fly = Get-FlyCmd
}
if (-not $fly) {
    throw "flyctl not found. Install from https://fly.io/docs/hands-on/install-flyctl/ then re-run."
}

Write-Host "Using: $fly" -ForegroundColor DarkGray
& $fly version

# Ensure logged in
$auth = & $fly auth whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nLog in to Fly.io (browser will open)..." -ForegroundColor Yellow
    & $fly auth login
}

if ($FirstTime) {
    Write-Host "`nCreating Fly app (region: sin) — accept defaults or name app 'ktmb-live-api'..." -ForegroundColor Cyan
    & $fly launch --no-deploy --copy-config --name ktmb-live-api --region sin
    if ($LASTEXITCODE -ne 0) {
        Write-Host "If app already exists, run without -FirstTime." -ForegroundColor Yellow
        exit $LASTEXITCODE
    }
}

if (-not $SkipSecrets) {
    $secrets = & $fly secrets list 2>&1 | Out-String
    if ($secrets -notmatch "API_KEY") {
        $clientKey = New-RandomKey
        $adminKey = New-RandomKey
        Write-Host "`nSetting API_KEY and ADMIN_API_KEY secrets..." -ForegroundColor Cyan
        & $fly secrets set "API_KEY=$clientKey" "ADMIN_API_KEY=$adminKey"
        $keysFile = Join-Path $BackendRoot "fly-keys.local.txt"
        @"
# Generated $(Get-Date -Format o) — DO NOT COMMIT. Use for Android build only.
API_BASE_URL=https://ktmb-live-api.fly.dev
API_KEY=$clientKey
ADMIN_API_KEY=$adminKey

flutter build appbundle --release `
  --dart-define=API_BASE_URL=https://ktmb-live-api.fly.dev `
  --dart-define=API_KEY=$clientKey
"@ | Set-Content -Path $keysFile -Encoding UTF8
        Write-Host "Keys saved to: $keysFile" -ForegroundColor Green
        Write-Host "Add fly-keys.local.txt to .gitignore if not already." -ForegroundColor Yellow
    } else {
        Write-Host "API_KEY secret already set — skipping." -ForegroundColor DarkGray
    }
}

Write-Host "`nDeploying..." -ForegroundColor Cyan
& $fly deploy
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`nHealth check:" -ForegroundColor Green
& $fly status
$hostname = (& $fly info --json | ConvertFrom-Json).Hostname
if ($hostname) {
    Write-Host "API: https://$hostname" -ForegroundColor Green
    Write-Host "Docs: https://$hostname/docs" -ForegroundColor Green
    Write-Host "Health: https://$hostname/api/health" -ForegroundColor Green
}

Write-Host "`nDone. Use fly-keys.local.txt for Android release build." -ForegroundColor Cyan
