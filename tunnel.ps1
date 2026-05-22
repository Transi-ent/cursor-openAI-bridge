# 使用 ngrok 将本机代理暴露为公网 HTTPS，供 Cursor 云端访问
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

function Get-ProxyPort {
    $defaultPort = 8787
    $configPath = Join-Path $Root "config.yaml"
    if (-not (Test-Path $configPath)) { return $defaultPort }
    $content = Get-Content $configPath -Raw
    if ($content -match '(?m)^\s*port:\s*(\d+)\s*$') { return [int]$Matches[1] }
    return $defaultPort
}

$port = Get-ProxyPort
$localUrl = "http://127.0.0.1:$port"

$listening = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if (-not $listening) {
    Write-Host "Proxy is not running on $localUrl"
    Write-Host "Start it first in another terminal: .\start.ps1"
    exit 1
}

$ngrok = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrok) {
    Write-Host @"
ngrok is not installed.

Install:
  winget install ngrok.ngrok

One-time auth (free account at https://dashboard.ngrok.com/get-started/your-authtoken):
  ngrok config add-authtoken <your-token>

Then run:
  .\tunnel.ps1
"@
    exit 1
}

Write-Host "Tunneling $localUrl via ngrok ..."
Write-Host ""
Write-Host "In the output below, find a line like:"
Write-Host "  Forwarding   https://xxxx.ngrok-free.app -> http://127.0.0.1:$port"
Write-Host ""
Write-Host "Cursor Override OpenAI Base URL = https://xxxx.ngrok-free.app/v1"
Write-Host "(replace xxxx with your actual subdomain)"
Write-Host ""
Write-Host "Press Ctrl+C to stop the tunnel."
Write-Host ""

& ngrok http $port
