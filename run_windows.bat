@echo off
setlocal
cd /d "%~dp0"
echo Starting cram2binxel_MD...
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 cram2binxel_MD.py
) else (
    python cram2binxel_MD.py
)
if errorlevel 1 (
    echo.
    echo Startup failed. Check startup_error.log in this folder.
    pause
)
endlocal
