# Installation Guide - MR. STARK

This guide explains how to set up and install MR. STARK on your Windows system.

## Prerequisites

- **Python 3.10 or newer** (download from https://www.python.org/)
  - Make sure to check "Add Python to PATH" during installation
- **Microphone** (for voice input)
- **Internet connection** (for Gemini API)

## Quick Start (Recommended)

### Method 1: Batch File (Easiest)

1. Right-click `install.bat` in the project folder
2. Select "Run as administrator"
3. Wait for installation to complete
4. Follow the post-installation instructions

### Method 2: PowerShell

1. Open PowerShell as Administrator
2. Navigate to the project folder:
   ```powershell
   cd "C:\Users\Admin\OneDrive\Desktop\Stark AI"
   ```
3. Run the installer:
   ```powershell
   powershell -ExecutionPolicy Bypass -File install.ps1
   ```
4. Wait for installation to complete

## Manual Installation

If you prefer to install manually:

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - **Command Prompt:**
     ```bash
     .venv\Scripts\activate.bat
     ```
   - **PowerShell:**
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file with your API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Getting Your API Key

1. Visit https://ai.google.dev/
2. Click "Get API key in Google AI Studio"
3. Create or select your project
4. Generate a new API key
5. Copy the key and paste it in the `.env` file

## Running the Application

### From Batch File Terminal
If you used `install.bat`, the virtual environment is already activated. Just run:
```bash
python mr_stark.py
```

### From PowerShell Terminal
If you used `install.ps1`, the virtual environment is already activated. Just run:
```bash
python mr_stark.py
```

### From Command Prompt/PowerShell (After Closing Terminal)
1. Activate the virtual environment:
   ```bash
   .venv\Scripts\activate
   ```
2. Run the application:
   ```bash
   python mr_stark.py
   ```

## Troubleshooting

### Issue: "Python is not installed or not in PATH"
**Solution:**
1. Install Python from https://www.python.org/
2. During installation, CHECK "Add Python to PATH"
3. Restart your computer
4. Try running the installer again

### Issue: "Permission denied" when running .bat
**Solution:**
- Right-click the `.bat` file
- Select "Run as administrator"

### Issue: "pyaudio could not be installed"
**Solution (Windows):**
1. Install Microsoft C++ Build Tools from https://visualstudio.microsoft.com/downloads/
2. Select "Desktop development with C++"
3. Complete the installation
4. Run the installer again

### Issue: "No microphone detected"
**Solution:**
1. Check Windows Sound settings: Settings → Sound → Volume and device preferences
2. Make sure a microphone is set as default
3. Check if microphone is muted or disabled
4. Try a different microphone device

### Issue: "GEMINI_API_KEY not found"
**Solution:**
1. Create or edit the `.env` file in the project root
2. Add: `GEMINI_API_KEY=your_actual_key_here`
3. Save the file
4. Restart the application

### Issue: "ModuleNotFoundError" for any package
**Solution:**
1. Make sure the virtual environment is activated
2. Run: `pip install -r requirements.txt`
3. Wait for all packages to install
4. Try running the app again

## Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| PySide6 | GUI Framework | >= 6.7.0 |
| google-genai | Gemini API | >= 0.1.0 |
| python-dotenv | Environment Config | >= 1.0.1 |
| pyttsx3 | Text-to-Speech | >= 2.90 |
| SpeechRecognition | Speech-to-Text | >= 3.10.0 |
| pyaudio | Microphone Input | >= 0.2.14 |

## Updating the Application

To update to the latest version:

1. Activate the virtual environment:
   ```bash
   .venv\Scripts\activate
   ```

2. Update dependencies:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. Run the application:
   ```bash
   python mr_stark.py
   ```

## Development Installation

If you want to contribute or modify the code:

1. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in editable mode
   ```

2. Install optional dev tools:
   ```bash
   pip install pytest black flake8 mypy
   ```

## Support

If you encounter issues:

1. Check this troubleshooting guide
2. Review the console output for error messages
3. Check the `.env` file for correct API key
4. Try restarting your computer
5. Report issues with error messages and system details

## Next Steps

After successful installation:

1. **Configure MR. STARK:**
   - Review `app/core/config.py` for settings
   - Adjust personality in `app/personality/voice.py`

2. **Test Voice Features:**
   - Enable Voice Mode in the application
   - Say "Hey Mr. Stark" to activate
   - Give a command

3. **Explore Capabilities:**
   - Try text mode (type commands)
   - Try voice mode (use microphone)
   - Check the console for system status

## Virtual Environment Tips

- **Activate before running:**
  Always activate the virtual environment before running the app or pip commands
  
- **Deactivate after use:**
  ```bash
  deactivate
  ```

- **Check activation status:**
  Your prompt should show `(.venv)` when activated

- **Reinstall packages:**
  If packages are corrupted:
  ```bash
  pip install --force-reinstall -r requirements.txt
  ```

---

**Installation Date:** September 1, 2026  
**Version:** 1.0.0  
**Last Updated:** September 1, 2026
