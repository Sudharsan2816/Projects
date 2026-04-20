# 🚀 AI Market Research Copilot - Dev Runner & Restarter
# This script kills existing processes on ports 8000 (Backend) and 8501 (Frontend) and restarts them.

$BackendPort = 8000
$FrontendPort = 8501

function Stop-ProcessOnPort($port) {
    $process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    if ($process) {
        Write-Host "Stopping process on port $port (PID: $process)..." -ForegroundColor Yellow
        Stop-Process -Id $process -Force
    }
}

Write-Host "--- Restarting AI Market Research Copilot ---" -ForegroundColor Cyan

# 1. Cleanup
Stop-ProcessOnPort $BackendPort
Stop-ProcessOnPort $FrontendPort

# 2. Start Backend (FastAPI)
Write-Host "Starting Backend on port $BackendPort..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'C:\Users\Welcome\Desktop\Projects\ai-market-research-copilot'; python -m uvicorn backend.main:app --reload --port $BackendPort" -WindowStyle Normal

# 3. Start Frontend (Streamlit)
Write-Host "Starting Frontend on port $FrontendPort..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'C:\Users\Welcome\Desktop\Projects\ai-market-research-copilot'; streamlit run frontend/app.py" -WindowStyle Normal

Write-Host "Done! Backend and Frontend are starting in separate windows." -ForegroundColor Cyan
Write-Host "Backend: http://localhost:$BackendPort"
Write-Host "Frontend: http://localhost:$FrontendPort"
