@echo off

REM Setup script for Immanuel MCP Server for Windows
REM This script helps with initial setup and configuration

setlocal

echo =========================================
echo Immanuel MCP Server Setup for Windows
echo =========================================

REM Check Python version
echo Checking Python version...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do (
    set PYTHON_VERSION=%%i
)

for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR_VERSION=%%a
    set MINOR_VERSION=%%b
)

if %MAJOR_VERSION% GEQ 3 if %MINOR_VERSION% GEQ 11 (
    echo OK (Python %PYTHON_VERSION%)
) else (
    echo ERROR
    echo Python 3.11 or higher is required. Found: Python %PYTHON_VERSION%
    exit /b 1
)

REM Check if uv is installed
echo Checking for uv...
where uv >nul 2>nul
if %errorlevel% equ 0 (
    echo OK
) else (
    echo NOT FOUND
    echo.
    set /p install_uv="uv is not installed. Would you like to install it? (y/n) "
    if /i "%install_uv%"=="y" (
        echo Installing uv...
        powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
        echo uv installed successfully!
    ) else (
        echo Please install uv manually from: https://github.com/astral-sh/uv
        exit /b 1
    )
)

REM Create virtual environment
echo.
echo Setting up virtual environment...
if not exist ".venv" (
    uv venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing dependencies...
uv pip install -r requirements.txt

REM Create directories
echo.
echo Creating necessary directories...
mkdir "%USERPROFILE%\.immanuel\ephemeris" >nul 2>nul
mkdir "%USERPROFILE%\.immanuel\cache" >nul 2>nul
mkdir "logs" >nul 2>nul

REM Download ephemeris files
echo.
echo Checking Swiss Ephemeris data files...
set EPHE_DIR=%USERPROFILE%\.immanuel\ephemeris

if not exist "%EPHE_DIR%\semo_18.se1" (
    set /p download_ephe="Ephemeris files not found. Would you like to download them? (y/n) "
    if /i "%download_ephe%"=="y" (
        echo Downloading ephemeris files...
        cd /d "%EPHE_DIR%"
        curl -O https://www.astro.com/ftp/swisseph/ephe/semo_18.se1
        curl -O https://www.astro.com/ftp/swisseph/ephe/sepl_18.se1
        cd /d "%~dp0"
        echo Ephemeris files downloaded successfully!
    ) else (
        echo WARNING: Ephemeris files are required for accurate calculations.
    )
) else (
    echo Ephemeris files found.
)

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo.
    echo Creating .env configuration file...
    (
        echo # Immanuel MCP Server Configuration
        echo.
        echo # Server settings
        echo IMMANUEL_SERVER_NAME=immanuel-mcp
        echo IMMANUEL_LOG_LEVEL=INFO
        echo.
        echo # Cache settings
        echo IMMANUEL_ENABLE_CACHE=true
        echo IMMANUEL_CACHE_MAX_SIZE=1000
        echo IMMANUEL_CACHE_TTL=3600
        echo.
        echo # Ephemeris path
        echo IMMANUEL_EPHEMERIS_PATH=%USERPROFILE%\.immanuel\ephemeris
        echo.
        echo # Default calculation settings
        echo IMMANUEL_DEFAULT_HOUSE_SYSTEM=placidus
        echo IMMANUEL_DEFAULT_ORB_CONJUNCTION=8.0
        echo IMMANUEL_DEFAULT_ORB_OPPOSITION=8.0
        echo IMMANUEL_DEFAULT_ORB_TRINE=8.0
        echo IMMANUEL_DEFAULT_ORB_SQUARE=8.0
        echo IMMANUEL_DEFAULT_ORB_SEXTILE=6.0
        echo IMMANUEL_DEFAULT_ORB_MINOR=3.0
        echo.
        echo # Timezone settings
        echo IMMANUEL_FALLBACK_TIMEZONE=UTC
        echo.
        echo # Performance settings
        echo IMMANUEL_MAX_BATCH_SIZE=100
        echo IMMANUEL_CALCULATION_TIMEOUT=30
    ) > .env
    echo .env file created.
) else (
    echo.
    echo .env file already exists.
)

echo.
echo =========================================
echo Setup Complete!
echo =========================================
echo.
echo Next steps:
echo 1. Configure Claude Desktop with the settings in claude-config.json
echo 2. Restart Claude Desktop
echo 3. The Immanuel MCP server should now be available
echo.
echo You can also:
echo - Run "python cli.py example" for a demo
echo - Run "python cli.py interactive" for interactive mode
echo - Run "python -m immanuel_mcp.api" to start the HTTP API server
echo - Run "python examples.py" to see usage examples
echo.
echo For more information, see README.md

endlocal
