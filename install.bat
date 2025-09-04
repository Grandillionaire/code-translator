@echo off
REM Code Translator Installation Script for Windows
REM Ensures proper setup of the application with all dependencies

echo ====================================================
echo Code Translator - Windows Installation Script
echo ====================================================
echo.

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please download and install Python 3.8 or newer from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check Python version
python -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)"
if %errorlevel% neq 0 (
    echo ERROR: Python 3.8 or newer is required
    echo Current version:
    python --version
    pause
    exit /b 1
)

echo Python installation OK
echo.

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing dependencies...
echo This may take a few minutes...
echo.

REM Core dependencies
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install core dependencies
    pause
    exit /b 1
)

REM Optional AI dependencies (continue on error)
echo.
echo Installing optional AI providers...
pip install openai anthropic google-generativeai 2>nul

REM Install the package
echo.
echo Installing Code Translator...
pip install -e .
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Code Translator
    pause
    exit /b 1
)

REM Check installation
echo.
echo Verifying installation...
python check_system.py

REM Create desktop shortcut
echo.
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Code Translator.lnk'); $Shortcut.TargetPath = '%CD%\start.bat'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.IconLocation = '%CD%\src\assets\icon.ico'; $Shortcut.Save()"

echo.
echo ====================================================
echo Installation completed successfully!
echo ====================================================
echo.
echo To run Code Translator:
echo 1. Double-click "Code Translator" on your desktop
echo 2. Or run: start.bat
echo 3. Or run: venv\Scripts\python.exe src\main.py
echo.
echo Don't forget to add your API keys in the settings!
echo.
pause