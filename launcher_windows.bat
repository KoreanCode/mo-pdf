@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" "launcher.py"
  exit /b 0
)

where pyw >nul 2>nul
if not errorlevel 1 (
  start "" pyw -3 "launcher.py"
  exit /b 0
)

where pythonw >nul 2>nul
if not errorlevel 1 (
  start "" pythonw "launcher.py"
  exit /b 0
)

where py >nul 2>nul
if not errorlevel 1 (
  start "" py -3 "launcher.py"
  exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
  start "" python "launcher.py"
  exit /b 0
)

mshta "javascript:alert('Python 3가 필요합니다. python.org에서 Python 3를 설치한 뒤 다시 실행하세요.');close()"
exit /b 1
