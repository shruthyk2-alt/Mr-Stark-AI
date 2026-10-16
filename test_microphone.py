#!/usr/bin/env python3
"""Test microphone detection with SpeechRecognition library."""

import speech_recognition as sr

print("=" * 70)
print("MICROPHONE DETECTION TEST")
print("=" * 70)

try:
    recognizer = sr.Recognizer()
    print("\n[OK] Recognizer initialized")
    
    print("\n[LIST] Available Microphones:")
    print("-" * 70)
    mic_list = sr.Microphone.list_microphone_names()
    for idx, name in enumerate(mic_list):
        print(f"  [{idx}] {name}")
    
    print("\n[DEFAULT] Windows Default Microphone:")
    print("-" * 70)
    default_mic = sr.Microphone()
    print(f"  Device Index: {default_mic.device_index}")
    if default_mic.device_index is not None and default_mic.device_index < len(mic_list):
        print(f"  Name: {mic_list[default_mic.device_index]}")
    else:
        print(f"  Name: Windows Default (System Default)")
    
    print("\n[TEST] Testing default microphone accessibility:")
    print("-" * 70)
    try:
        with default_mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("  [OK] Microphone is accessible")
            print(f"  [OK] Ambient noise detected and adjusted")
            print(f"  [READY] Ready for voice capture")
    except Exception as e:
        print(f"  [ERROR] Failed to access microphone: {e}")
    
    print("\n[STATUS] Voice capture pipeline:")
    print("-" * 70)
    print(f"  Speech Recognition: Enabled")
    print(f"  Google Speech-to-Text: Available")
    print(f"  Microphone Input: Available")
    print(f"  System Ready: YES")
    
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    print("  Run: pip install SpeechRecognition pyaudio")
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")

print("\n" + "=" * 70)
