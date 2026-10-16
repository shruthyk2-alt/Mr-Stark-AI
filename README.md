# MR. STARK

MR. STARK is a personal AI desktop assistant powered by Google's Gemini API. It features a polished GUI with voice and text interaction, wake-word activation, and continuous conversation support. Built with PySide6 for a modern desktop experience.

## Quick Start (Windows)

### Fastest Way to Get Started

1. **Run the installer:**
   - Right-click `install.bat` → "Run as administrator"
   - Or open PowerShell and run: `powershell -ExecutionPolicy Bypass -File install.ps1`

2. **Add your API key:**
   - Get it from https://ai.google.dev/
   - Edit `.env` file: `GEMINI_API_KEY=your_key_here`

3. **Start using:**
   - Run: `python mr_stark.py`
   - Press "Voice: On"
   - Say: "Hey Mr. Stark"
   - Ask a question!

For detailed installation instructions, see [INSTALLATION.md](INSTALLATION.md)

## Features

### Voice Interaction
- ✓ Continuous voice listening with wake-word activation
- ✓ "Hey Mr. Stark" wake phrase (local, no API calls)
- ✓ Automatic return to standby after 30 seconds of silence
- ✓ Male David voice TTS with microphone suppression
- ✓ Fuzzy wake-word matching (handles mishearings)

### Conversation
- ✓ Unified text/voice pipeline to Gemini API
- ✓ Conversation history with context
- ✓ MR. STARK personality (witty, confident, blunt)
- ✓ Real-time datetime awareness
- ✓ Natural conversation flow

### Technology
- ✓ Modern PySide6 GUI with animated elements
- ✓ Google Gemini 3.6 Flash API
- ✓ SpeechRecognition library with Google STT
- ✓ pyttsx3 text-to-speech engine
- ✓ Multi-threaded architecture for responsiveness

## Project Structure

```
mr_stark.py                     # Application entry point
requirements.txt                # Python dependencies
.env                           # Configuration (API key)
install.bat                    # Windows installer
install.ps1                    # PowerShell installer
setup.py                       # Python package config
pyproject.toml                 # Modern project config
verify_installation.py         # Verification script

app/
  core/
    config.py                  # Configuration
    orchestrator.py            # System orchestration
  ui/
    main_window.py             # Main GUI + voice pipeline
  tools/
    registry.py                # Tool definitions
  permissions/
    guard.py                   # Permission checks
  personality/
    voice.py                   # MR. STARK personality
```

## Installation Methods

### Method 1: Windows Installer (Recommended)
```bash
# Batch file (GUI)
install.bat

# Or PowerShell
powershell -ExecutionPolicy Bypass -File install.ps1
```

### Method 2: Manual Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate it
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
# Edit .env: GEMINI_API_KEY=your_key_here

# Run application
python mr_stark.py
```

### Method 3: Development Mode
```bash
# Install in editable mode with dev tools
pip install -e ".[dev]"

# Run application
python mr_stark.py
```

## Verification

After installation, verify everything is set up correctly:

```bash
python verify_installation.py
```

Expected output: `6/6 checks passed`

## Usage

### Text Mode
1. Type your message in the console
2. Press Enter
3. MR. STARK responds

### Voice Mode
1. Press "Voice: On" button
2. Say "Hey Mr. Stark" to activate
3. Say your command or question
4. Listen to MR. STARK's response
5. Continue speaking (auto-listens for 30 seconds)
6. Say "Hey Mr. Stark" again or press "Voice: Off"

## Configuration

### API Key
Add your Gemini API key to `.env`:
```
GEMINI_API_KEY=your_api_key_from_https://ai.google.dev/
```

### Wake-Word Activation
Disable in code if preferred (use Voice On/Off only):
```python
# In app/ui/main_window.py
window.wake_word_enabled = False
```

### Inactivity Timeout
Change how long voice stays active (default: 30 seconds):
```python
# In app/ui/main_window.py
window.inactivity_timeout_seconds = 60
```

## System Requirements

- **OS:** Windows 10 or later
- **Python:** 3.10+ (3.11 or 3.12 recommended)
- **RAM:** 2GB minimum (4GB+ recommended)
- **Disk:** 500MB for dependencies
- **Internet:** Required for Gemini API
- **Audio:** Microphone + speakers/headphones for voice

## Troubleshooting

### Installation Issues
See [INSTALLATION.md](INSTALLATION.md#troubleshooting) for detailed troubleshooting including:
- Python not found
- Permission errors
- Missing dependencies
- Microphone issues
- API key problems

### Voice Not Working
1. Check Windows Sound settings (Settings → Sound)
2. Verify a microphone is set as default
3. Test with `python test_microphone.py`
4. Check console for [VOICE] error messages

### No Gemini Response
1. Verify `GEMINI_API_KEY` in `.env` file
2. Check internet connection
3. Verify API key is valid at https://ai.google.dev/
4. Check console for [ERROR] messages

## Documentation

- [INSTALLATION.md](INSTALLATION.md) - Complete setup guide
- [INSTALLER_README.md](INSTALLER_README.md) - Installer details
- [WAKE_WORD_SYSTEM.md](WAKE_WORD_SYSTEM.md) - Wake-word documentation
- [VOICE_PIPELINE_FIX_REPORT.txt](VOICE_PIPELINE_FIX_REPORT.txt) - Voice architecture

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| PySide6 | ≥6.7.0 | GUI Framework |
| google-genai | ≥0.1.0 | Gemini API Client |
| python-dotenv | ≥1.0.1 | Environment Config |
| pyttsx3 | ≥2.90 | Text-to-Speech |
| SpeechRecognition | ≥3.10.0 | Speech Recognition |
| pyaudio | ≥0.2.14 | Microphone Input |

## Development

### Setup Development Environment
```bash
pip install -e ".[dev]"
```

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
```

### Type Checking
```bash
mypy app/
```

## Performance

- **Startup:** ~2-3 seconds
- **Voice recognition:** ~1-2 seconds per utterance
- **Gemini response time:** ~2-5 seconds (depends on API)
- **TTS playback:** Real-time (speaks as text is generated)
- **Memory usage:** ~200-300MB idle

## Known Limitations

- Windows only (can be adapted for macOS/Linux)
- Requires internet connection for API
- Microphone required for voice features
- Single conversation instance (no multi-window)

## Future Enhancements

- [ ] macOS/Linux support
- [ ] Persistent conversation history
- [ ] Custom wake-word configuration
- [ ] Voice profile personalization
- [ ] Tool integration system
- [ ] Plugin architecture
- [ ] Desktop notifications
- [ ] System tray mode

## License

MIT License - See LICENSE file for details

## Credits

- **Frontend:** PySide6 (Qt for Python)
- **AI:** Google Gemini API
- **Voice:** Google Speech-to-Text + pyttsx3 TTS
- **Design:** Modern desktop UI with polished interactions

---

**Status:** Production Ready (v1.0.0)  
**Last Updated:** September 1, 2026  
**Maintainer:** Shruthy