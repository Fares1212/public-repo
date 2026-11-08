@echo off
cd /d "%~dp0"
where pyw >nul 2>nul
if not errorlevel 1 (
    start "" pyw -3 "%~dp0main.py"
    exit /b
)
where pythonw >nul 2>nul
if not errorlevel 1 (
    start "" pythonw "%~dp0main.py"
    exit /b
)
echo Install Python 3.10 or newer from https://www.python.org/downloads/windows/
echo Include Tcl/Tk and the Python launcher, then run this file again.
pause
