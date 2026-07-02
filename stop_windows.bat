@echo off
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$roots = @((Get-Location).Path); if ($env:LOCALAPPDATA) { $roots += Join-Path $env:LOCALAPPDATA 'OrangePdfBlur' }; $ids = @(); $ports = @(5000); foreach ($root in $roots) { foreach ($pidPath in @((Join-Path $root 'server.pid'), (Join-Path $root 'runtime\server.pid'))) { if (Test-Path $pidPath) { $raw = Get-Content $pidPath -ErrorAction SilentlyContinue; if ($raw -match '^\d+$') { $ids += [int]$raw } } }; $portPath = Join-Path $root 'runtime\server.port'; if (Test-Path $portPath) { $rawPort = Get-Content $portPath -ErrorAction SilentlyContinue; if ($rawPort -match '^\d+$') { $ports += [int]$rawPort } } }; foreach ($port in ($ports | Select-Object -Unique)) { $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue; if ($conn) { $ids += $conn.OwningProcess } }; $ids = $ids | Select-Object -Unique; foreach ($id in $ids) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }; if ($ids.Count -gt 0) { exit 0 } else { exit 2 }"
set STOP_EXIT=%ERRORLEVEL%
del "server.pid" >nul 2>nul
del "runtime\server.pid" >nul 2>nul
if defined LOCALAPPDATA (
  del "%LOCALAPPDATA%\OrangePdfBlur\server.pid" >nul 2>nul
  del "%LOCALAPPDATA%\OrangePdfBlur\runtime\server.pid" >nul 2>nul
  del "%LOCALAPPDATA%\OrangePdfBlur\runtime\server.port" >nul 2>nul
)

if "%STOP_EXIT%"=="0" (
  echo Server stopped.
) else (
  echo Server process was not found.
)

pause
exit /b 0
