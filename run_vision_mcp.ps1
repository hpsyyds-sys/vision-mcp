$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $ScriptDir

try {
    & python server.py
} catch {
    Write-Error $_.Exception.Message
    exit 1
} finally {
    Pop-Location
}
