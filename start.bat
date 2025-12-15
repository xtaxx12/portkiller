@echo off
echo ========================================
echo    PortKiller - Port Management Tool
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if venv exists, if not create it
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo [INFO] Installing dependencies...
pip install -r requirements.txt --quiet

REM Run the application
echo.
echo [INFO] Starting PortKiller...
echo.
python main.py

pause
