@echo off
REM Code Translator launcher for Windows

echo Starting Code Translator...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed!
    echo Please install Python 3.8 or newer from https://www.python.org
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "src\main.py" (
    echo Error: Cannot find src\main.py
    echo Please run this script from the code-translator directory
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import PyQt6" 2>nul
if %errorlevel% neq 0 (
    echo Dependencies not installed. Installing now...
    pip install -r requirements.txt
)

REM Launch the application
python src\main.py %*