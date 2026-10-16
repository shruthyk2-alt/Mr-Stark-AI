@echo off
REM MR. STARK Installer for Windows
REM This script sets up the environment and installs all dependencies

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo                     MR. STARK - Windows Installation
echo ============================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [OK] Python detected
python --version

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo.
    echo [SETUP] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment
echo.
echo [SETUP] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

REM Upgrade pip
echo.
echo [SETUP] Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel --quiet
if errorlevel 1 (
    echo [WARNING] pip upgrade had issues, continuing anyway...
)
echo [OK] pip upgraded

REM Install requirements
echo.
echo [SETUP] Installing dependencies from requirements.txt...
echo This may take a few minutes...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)
echo.
echo [OK] Dependencies installed successfully

REM Verify installation
echo.
echo [VERIFY] Checking critical dependencies...
python -c "import PySide6; print('[OK] PySide6 installed')" || (echo [ERROR] PySide6 not found & goto :error)
python -c "import google.genai; print('[OK] google-genai installed')" || (echo [ERROR] google-genai not found & goto :error)
python -c "import speech_recognition; print('[OK] SpeechRecognition installed')" || (echo [ERROR] SpeechRecognition not found & goto :error)
python -c "import pyttsx3; print('[OK] pyttsx3 installed')" || (echo [ERROR] pyttsx3 not found & goto :error)

echo.
echo [VERIFY] Checking for .env file...
if not exist ".env" (
    echo [WARNING] .env file not found
    echo [INFO] Creating template .env file...
    (
        echo # MR. STARK Configuration
        echo # Get your API key from: https://ai.google.dev/
        echo GEMINI_API_KEY=your_api_key_here
    ) > .env
    echo [OK] Template .env created - please add your GEMINI_API_KEY
) else (
    echo [OK] .env file exists
)

echo.
echo ============================================================================
echo                        Installation Complete!
echo ============================================================================
echo.
echo Next steps:
echo 1. Add your GEMINI_API_KEY to the .env file (if not already set)
echo    - Get key from: https://ai.google.dev/
echo 2. Run the application:
echo    python mr_stark.py
echo.
echo Virtual environment is activated in this terminal.
echo.
pause
exit /b 0

:error
echo.
echo [ERROR] Installation failed
echo Please check the error messages above
pause
exit /b 1
