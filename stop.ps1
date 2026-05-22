$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

function Get-ProxyPort {
    $defaultPort = 8787
    $configPath = Join-Path $Root "config.yaml"
    if (-not (Test-Path $configPath)) {
        return $defaultPort
    }
    $content = Get-Content $configPath -Raw
    if ($content -match '(?m)^\s*port:\s*(\d+)\s*$') {
        return [int]$Matches[1]
    }
    return $defaultPort
}

$port = Get-ProxyPort
Write-Host "Stopping Cursor OpenAI Bridge on port $port ..."

$connections = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
if ($connections.Count -eq 0) {
    Write-Host "No process is listening on port $port (proxy may already be stopped)."
    exit 0
}

$pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
$stopped = 0

foreach ($procId in $pids) {
    try {
        $proc = Get-Process -Id $procId -ErrorAction Stop
        Write-Host "Stopping PID $procId ($($proc.ProcessName)) ..."
        Stop-Process -Id $procId -Force -ErrorAction Stop
        $stopped++
    }
    catch {
        Write-Warning "Could not stop PID ${procId}: $_"
    }
}

if ($stopped -gt 0) {
    Write-Host "Stopped $stopped process(es). Proxy is no longer running on port $port."
}
else {
    Write-Host "No process could be stopped."
    exit 1
}
