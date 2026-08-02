@echo off
setlocal

cd /d "%~dp0"
py -3.12 -m pip install ".[build]"
if errorlevel 1 exit /b %errorlevel%

py -3.12 -m PyInstaller --noconfirm --clean CafePOS.spec
if errorlevel 1 exit /b %errorlevel%

set "RELEASE_DIR=dist\CafePOS"
if not exist "%RELEASE_DIR%\logs" mkdir "%RELEASE_DIR%\logs"

if exist "cafepos.db" (
    copy /Y "cafepos.db" "%RELEASE_DIR%\cafepos.db" >nul
) else (
    py -3.12 -c "import sqlite3; sqlite3.connect(r'dist/CafePOS/cafepos.db').close()"
)
if errorlevel 1 exit /b %errorlevel%

if exist "config.json" copy /Y "config.json" "%RELEASE_DIR%\config.json" >nul

py -3.12 work\verify_packaging.py
if errorlevel 1 exit /b %errorlevel%

echo.
echo CafePOS package created in %RELEASE_DIR%
echo cafepos.db, config.json, and logs are external to CafePOS.exe.
