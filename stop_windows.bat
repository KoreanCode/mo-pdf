@echo off
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ids = @(); foreach ($pidPath in @('server.pid', 'runtime\server.pid')) { if (Test-Path $pidPath) { $raw = Get-Content $pidPath -ErrorAction SilentlyContinue; if ($raw -match '^\d+$') { $ids += [int]$raw } } }; $conn = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue; if ($conn) { $ids += $conn.OwningProcess }; $ids = $ids | Select-Object -Unique; foreach ($id in $ids) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }; if ($ids.Count -gt 0) { exit 0 } else { exit 2 }"
set STOP_EXIT=%ERRORLEVEL%
del "server.pid" >nul 2>nul
del "runtime\server.pid" >nul 2>nul

if "%STOP_EXIT%"=="0" (
  echo Server stopped.
) else (
  echo Server process was not found.
)

pause
exit /b 0
