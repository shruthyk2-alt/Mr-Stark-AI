#!/usr/bin/env python3
import pyttsx3
import google.genai as genai

print("=" * 60)
print("DEBUGGING TTS VOICES")
print("=" * 60)

engine = pyttsx3.init()
voices = engine.getProperty('voices')

print(f"\nTotal voices available: {len(voices)}\n")

for i, voice in enumerate(voices):
    print(f"Voice {i}:")
    print(f"  ID: {voice.id}")
    print(f"  Name: {voice.name}")
    print(f"  Gender: {voice.gender}")
    print()

print("=" * 60)
print("DEBUGGING GEMINI SDK")
print("=" * 60)

# Check the actual signature of generate_content
import inspect
sig = inspect.signature(genai.Client.models.generate_content)
print(f"\ngenerate_content signature: {sig}")

# Check GenerateContentConfig
from google.genai import types
print(f"\nGenerateContentConfig fields:")
if hasattr(types.GenerateContentConfig, '__annotations__'):
    for field, typ in types.GenerateContentConfig.__annotations__.items():
        print(f"  {field}: {typ}")
else:
    print("  (no annotations available)")

print("\n" + "=" * 60)
