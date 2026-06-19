@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo Starting Orange Factory Document Blur...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 (
  echo Server is already running.
  start "" "http://127.0.0.1:5000"
  echo.
  echo Run stop_windows.vbs or stop_windows.bat to stop the server.
  pause
  exit /b 0
)

if exist "server.pid" (
  set /p SERVER_PID=<server.pid
  powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-Process -Id !SERVER_PID! -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
  if not errorlevel 1 (
    echo Server is already running.
    start "" "http://127.0.0.1:5000"
    echo.
    echo Run stop_windows.vbs or stop_windows.bat to stop the server.
    pause
    exit /b 0
  )
  del "server.pid" >nul 2>nul
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  py -3 -m venv .venv
  if errorlevel 1 (
    python -m venv .venv
  )
  if errorlevel 1 (
    echo.
    echo Python 3 was not found.
    echo Install Python from https://www.python.org/downloads/ and run this again.
    pause
    exit /b 1
  )
)

echo Checking required packages...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Package installation failed.
  echo Check your internet connection and run this again.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$python = if (Test-Path '.\.venv\Scripts\pythonw.exe') { '.\.venv\Scripts\pythonw.exe' } else { '.\.venv\Scripts\python.exe' }; $p = Start-Process -FilePath $python -ArgumentList 'app.py' -WorkingDirectory (Get-Location) -WindowStyle Hidden -PassThru; Set-Content -Path 'server.pid' -Value $p.Id -Encoding ASCII"
if errorlevel 1 (
  echo.
  echo Failed to start the server.
  echo Check server.err.log for details.
  pause
  exit /b 1
)

timeout /t 2 /nobreak >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if errorlevel 1 (
  echo.
  echo The server stopped immediately.
  echo Check server.err.log for details.
  del "server.pid" >nul 2>nul
  pause
  exit /b 1
)

start "" "http://127.0.0.1:5000"
echo.
echo Server is running.
echo http://127.0.0.1:5000
echo.
echo Run stop_windows.vbs or stop_windows.bat to stop the server.
pause
exit /b 0
