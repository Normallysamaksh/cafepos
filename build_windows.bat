@echo off
setlocal

cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
    set "PY_CMD=py -3.12"
) else (
    set "PY_CMD=python"
)

%PY_CMD% -m pip install ".[build]"
if errorlevel 1 exit /b %errorlevel%

%PY_CMD% -m PyInstaller --noconfirm --clean CafePOS.spec
if errorlevel 1 exit /b %errorlevel%

set "RELEASE_DIR=dist\CafePOS"
if not exist "%RELEASE_DIR%\logs" mkdir "%RELEASE_DIR%\logs"

if exist "cafepos.db" (
    copy /Y "cafepos.db" "%RELEASE_DIR%\cafepos.db" >nul
) else (
    %PY_CMD% -c "import sqlite3; sqlite3.connect(r'dist/CafePOS/cafepos.db').close()"
)
if errorlevel 1 exit /b %errorlevel%

if exist "config.json" copy /Y "config.json" "%RELEASE_DIR%\config.json" >nul
if exist "default_menu.json" copy /Y "default_menu.json" "%RELEASE_DIR%\default_menu.json" >nul

%PY_CMD% work\verify_packaging.py
if errorlevel 1 exit /b %errorlevel%

echo.
echo CafePOS package created in %RELEASE_DIR%
echo cafepos.db, config.json, and logs are external to CafePOS.exe.
