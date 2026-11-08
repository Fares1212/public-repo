@echo off
setlocal
title Chest Counter
cd /d "%~dp0"
if not exist "%~dp0main.py" (
    echo Chest Counter files are missing. Extract the entire ZIP before launching.
    pause
    exit /b 1
)

rem A launcher can exist even when the Python installation it remembers is gone.
rem Test an actual interpreter and Tk before choosing it. Use the console launcher
rem so a stale registration cannot produce a pythonw error dialog.
set "_CHEST_STARTED="
call :try_python py -3
if defined _CHEST_STARTED exit /b 0
call :try_python python
if defined _CHEST_STARTED exit /b 0
call :try_python python3
if defined _CHEST_STARTED exit /b 0

rem A stale default in py must not hide a working older Python installation.
for %%V in (3.15 3.14 3.13 3.12 3.11 3.10) do (
    if not defined _CHEST_STARTED call :try_python py -%%V
)
if defined _CHEST_STARTED exit /b 0

rem Also support the standard installer locations when Python is absent from PATH.
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*" "%ProgramFiles%\Python*" "%ProgramFiles(x86)%\Python*") do (
    if not defined _CHEST_STARTED call :try_python "%%~fD\python.exe"
)
if defined _CHEST_STARTED exit /b 0

echo.
echo No working Python 3.10+ installation with Tcl/Tk was found.
echo Your Python launcher may point to an installation that was moved or deleted.
echo Install or repair Python from:
echo https://www.python.org/downloads/windows/
echo Keep Tcl/Tk enabled and select Add python.exe to PATH in the installer.
echo Then close this window and run Launch Chest Counter.bat again.
pause
exit /b 1

:try_python
"%~1" %~2 -c "import sys; sys.exit(1) if sys.version_info < (3, 10) else None; import tkinter" >nul 2>nul
if errorlevel 1 exit /b
set "_CHEST_STARTED=1"
echo Starting Chest Counter. Keep this window open while using the overlay.
"%~1" %~2 "%~dp0main.py"
if errorlevel 1 (
    echo.
    echo Chest Counter could not start. The error is shown above.
    pause
)
exit /b
