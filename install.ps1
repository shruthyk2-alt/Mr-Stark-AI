# MR. STARK Installer for Windows (PowerShell)
# Run with: powershell -ExecutionPolicy Bypass -File install.ps1

Write-Host "`n" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "                     MR. STARK - Windows Installation" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "`n"

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from https://www.python.org/" -ForegroundColor Red
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "`n[SETUP] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "`n[OK] Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`n[SETUP] Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to activate virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] Virtual environment activated" -ForegroundColor Green

# Upgrade pip
Write-Host "`n[SETUP] Upgrading pip, setuptools, and wheel..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] pip upgrade had issues, continuing anyway..." -ForegroundColor Yellow
}
Write-Host "[OK] pip upgraded" -ForegroundColor Green

# Install requirements
Write-Host "`n[SETUP] Installing dependencies from requirements.txt..." -ForegroundColor Yellow
Write-Host "This may take a few minutes...`n"
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[ERROR] Failed to install dependencies" -ForegroundColor Red
    Write-Host "Please check your internet connection and try again" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "`n[OK] Dependencies installed successfully" -ForegroundColor Green

# Verify installation
Write-Host "`n[VERIFY] Checking critical dependencies..." -ForegroundColor Yellow
try {
    python -c "import PySide6; print('[OK] PySide6 installed')" | Write-Host -ForegroundColor Green
} catch {
    Write-Host "[ERROR] PySide6 not found" -ForegroundColor Red
    exit 1
}

try {
    python -c "import google.genai; print('[OK] google-genai installed')" | Write-Host -ForegroundColor Green
} catch {
    Write-Host "[ERROR] google-genai not found" -ForegroundColor Red
    exit 1
}

try {
    python -c "import speech_recognition; print('[OK] SpeechRecognition installed')" | Write-Host -ForegroundColor Green
} catch {
    Write-Host "[ERROR] SpeechRecognition not found" -ForegroundColor Red
    exit 1
}

try {
    python -c "import pyttsx3; print('[OK] pyttsx3 installed')" | Write-Host -ForegroundColor Green
} catch {
    Write-Host "[ERROR] pyttsx3 not found" -ForegroundColor Red
    exit 1
}

# Check for .env file
Write-Host "`n[VERIFY] Checking for .env file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "[WARNING] .env file not found" -ForegroundColor Yellow
    Write-Host "[INFO] Creating template .env file..." -ForegroundColor Cyan
    
    @"
# MR. STARK Configuration
# Get your API key from: https://ai.google.dev/
GEMINI_API_KEY=your_api_key_here
"@ | Out-File -FilePath ".env" -Encoding UTF8
    
    Write-Host "[OK] Template .env created - please add your GEMINI_API_KEY" -ForegroundColor Green
} else {
    Write-Host "[OK] .env file exists" -ForegroundColor Green
}

Write-Host "`n" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "                        Installation Complete!" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "`n"

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Add your GEMINI_API_KEY to the .env file (if not already set)" -ForegroundColor White
Write-Host "   - Get key from: https://ai.google.dev/" -ForegroundColor Cyan
Write-Host "2. Run the application:" -ForegroundColor White
Write-Host "   python mr_stark.py" -ForegroundColor Cyan
Write-Host "`n"
Write-Host "Virtual environment is activated in this terminal." -ForegroundColor Green
Write-Host "`n"

Read-Host "Press Enter to close"
