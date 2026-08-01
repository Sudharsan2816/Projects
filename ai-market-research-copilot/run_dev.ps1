$BackendPort = 8000

function Stop-ProcessOnPort($Port) {
    $processIds = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $processIds) {
        Stop-Process -Id $processId -Force
    }
}

Stop-ProcessOnPort $BackendPort

Write-Host "Starting AI Market Research Copilot on http://localhost:$BackendPort" -ForegroundColor Green
Start-Process powershell `
    -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot'; python -m uvicorn backend.main:app --reload --port $BackendPort" `
    -WindowStyle Normal
