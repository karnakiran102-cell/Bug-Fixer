@echo off
REM Multi-Agent SDLC System - Windows Setup Script
REM This script automates the installation process

echo.
echo ============================================================================
echo MULTI-AGENT SDLC SYSTEM - SETUP SCRIPT (Windows)
echo ============================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo ✓ Python detected
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists
) else (
    python -m venv venv
    echo ✓ Virtual environment created
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel
echo ✓ pip upgraded
echo.

REM Install requirements
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed successfully
echo.

REM Create .env file
echo.
echo ============================================================================
echo CONFIGURATION SETUP
echo ============================================================================
echo.
echo A .env file is required to store your API keys.
echo.

if exist .env (
    echo .env file already exists
) else (
    echo Creating .env file from template...
    if exist .env.example (
        copy .env.example .env
        echo ✓ .env file created
    ) else (
        echo ERROR: .env.example not found
    )
)

echo.
echo ============================================================================
echo IMPORTANT: API KEY CONFIGURATION
echo ============================================================================
echo.
echo You need to add your LLM API keys to the .env file.
echo.
echo OPTIONS:
echo   1. OpenAI (GPT-4): https://platform.openai.com/api-keys
echo   2. Anthropic Claude: https://console.anthropic.com/
echo   3. Google Gemini: https://ai.google.dev/
echo.
echo Open .env file and add your API key:
echo   OPENAI_API_KEY=sk-your-key-here
echo.

REM Ask to open .env file
set /p OPEN_ENV="Would you like to open .env file now? (y/n): "
if /i "%OPEN_ENV%"=="y" (
    notepad .env
)

echo.
echo ============================================================================
echo SETUP COMPLETE
echo ============================================================================
echo.
echo Next steps:
echo   1. Make sure your API keys are set in .env file
echo   2. Run the system: python agents_sdlc.py
echo   3. Or explore examples: python examples.py
echo.
echo For more information, see README.md
echo.

pause
