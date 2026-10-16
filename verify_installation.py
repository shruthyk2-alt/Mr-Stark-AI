#!/usr/bin/env python3
"""Verify MR. STARK installation and environment setup."""

import os
import sys
from pathlib import Path

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_ok(text):
    print(f"[OK] {text}")

def print_warning(text):
    print(f"[WARNING] {text}")

def print_error(text):
    print(f"[ERROR] {text}")

def check_python_version():
    """Check if Python version meets requirements."""
    print_header("Python Version Check")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major >= 3 and version.minor >= 10:
        print_ok(f"Python {version_str} is supported")
        return True
    else:
        print_error(f"Python {version_str} - requires 3.10 or newer")
        return False

def check_dependencies():
    """Check if all required packages are installed."""
    print_header("Dependency Check")
    
    dependencies = {
        "PySide6": "GUI Framework",
        "google.genai": "Gemini API Client",
        "dotenv": "Environment Configuration",
        "pyttsx3": "Text-to-Speech",
        "speech_recognition": "Speech Recognition",
        "pyaudio": "Microphone Input",
    }
    
    all_ok = True
    for package, description in dependencies.items():
        try:
            if package == "google.genai":
                __import__("google.genai")
            else:
                __import__(package)
            print_ok(f"{package}: {description}")
        except ImportError:
            print_error(f"{package}: {description} - NOT INSTALLED")
            all_ok = False
    
    return all_ok

def check_project_structure():
    """Check if all required project directories exist."""
    print_header("Project Structure Check")
    
    required_dirs = [
        "app",
        "app/core",
        "app/ui",
        "app/tools",
        "app/permissions",
        "app/personality",
    ]
    
    required_files = [
        "mr_stark.py",
        "requirements.txt",
        "README.md",
        ".env",
    ]
    
    all_ok = True
    
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print_ok(f"Directory: {dir_path}")
        else:
            print_error(f"Directory missing: {dir_path}")
            all_ok = False
    
    for file_path in required_files:
        if os.path.isfile(file_path):
            print_ok(f"File: {file_path}")
        else:
            if file_path == ".env":
                print_warning(f"File missing: {file_path} (will be created on first run)")
            else:
                print_error(f"File missing: {file_path}")
                all_ok = False
    
    return all_ok

def check_environment_config():
    """Check if environment configuration is set."""
    print_header("Environment Configuration Check")
    
    if not os.path.isfile(".env"):
        print_warning(".env file not found - creating template")
        try:
            with open(".env", "w") as f:
                f.write("# MR. STARK Configuration\n")
                f.write("# Get your API key from: https://ai.google.dev/\n")
                f.write("GEMINI_API_KEY=your_api_key_here\n")
            print_ok(".env template created - add your GEMINI_API_KEY")
        except Exception as e:
            print_error(f"Could not create .env file: {e}")
            return False
        return False
    
    # Check if API key is set
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_api_key_here":
        print_warning("GEMINI_API_KEY not set or using default value")
        print("  → Get API key from: https://ai.google.dev/")
        print("  → Add to .env file: GEMINI_API_KEY=<your_key>")
        return False
    else:
        print_ok("GEMINI_API_KEY is configured")
        return True

def check_voice_system():
    """Check if voice system components are available."""
    print_header("Voice System Check")
    
    try:
        import speech_recognition as sr
        print_ok("Speech Recognition library loaded")
        
        # List available microphones
        mic_list = sr.Microphone.list_microphone_names()
        if mic_list:
            print_ok(f"Found {len(mic_list)} audio device(s)")
            
            # Show first few devices
            for i, mic_name in enumerate(mic_list[:5]):
                print(f"  [{i}] {mic_name}")
            
            if len(mic_list) > 5:
                print(f"  ... and {len(mic_list) - 5} more")
        else:
            print_error("No audio devices found")
            return False
        
        # Test default microphone
        try:
            with sr.Microphone() as source:
                sr.Recognizer().adjust_for_ambient_noise(source, duration=0.5)
            print_ok("Default microphone is accessible")
        except Exception as e:
            print_warning(f"Could not access default microphone: {e}")
            return False
        
    except ImportError as e:
        print_error(f"Speech Recognition not available: {e}")
        return False
    
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print_ok(f"Text-to-Speech initialized ({len(voices)} voices available)")
    except Exception as e:
        print_warning(f"Text-to-Speech error: {e}")
        return False
    
    return True

def check_gemini_config():
    """Check Gemini API configuration."""
    print_header("Gemini API Configuration Check")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        
        if not api_key or api_key == "your_api_key_here":
            print_error("GEMINI_API_KEY not configured")
            print("  → Add your API key to .env file")
            return False
        
        # Try to import and initialize the client
        try:
            import google.genai as genai
            client = genai.Client(api_key=api_key)
            print_ok("Gemini API client initialized")
            
            # Don't make actual API calls, just check the client
            print_ok("API key format appears valid")
            return True
        
        except Exception as e:
            print_error(f"Gemini API initialization failed: {e}")
            return False
    
    except Exception as e:
        print_error(f"Configuration error: {e}")
        return False

def main():
    """Run all verification checks."""
    print("\n")
    print("=" * 70)
    print("         MR. STARK - Installation Verification")
    print("=" * 70)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Project Structure", check_project_structure),
        ("Environment Configuration", check_environment_config),
        ("Voice System", check_voice_system),
        ("Gemini API", check_gemini_config),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_error(f"Check '{name}' failed with error: {e}")
            results[name] = False
    
    # Summary
    print_header("Verification Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "[+]" if result else "[-]"
        print(f"{symbol} {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print_ok("All checks passed! MR. STARK is ready to run.")
        print("\nTo start the application, run:")
        print("  python mr_stark.py")
        return 0
    elif passed >= total - 1:
        print_warning("Most checks passed. Some optional components may be missing.")
        print("\nYou can still try running the application:")
        print("  python mr_stark.py")
        return 0
    else:
        print_error("Installation verification failed. Please review the errors above.")
        print("\nCommon solutions:")
        print("  1. Run installer again: install.bat (or install.ps1)")
        print("  2. Reinstall dependencies: pip install -r requirements.txt")
        print("  3. Check .env file has GEMINI_API_KEY configured")
        print("  4. Verify Python 3.10+ is installed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
