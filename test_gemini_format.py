#!/usr/bin/env python3
import google.genai as genai
from google.genai.types import Content, Part

# Test the structure expected by google-genai
print("Testing google-genai message format...")

# Try creating a Content object
try:
    content = Content(role="user", parts=[Part(text="Hello")])
    print(f"✓ Content object created: {content}")
except Exception as e:
    print(f"✗ Error creating Content: {e}")

# Check if we can pass simpler format
print("\nTesting simpler formats...")
test_messages = [
    "Just a string",
    {"role": "user", "parts": [{"text": "Message"}]},
    {"role": "user", "content": "Message"},
]

for i, msg in enumerate(test_messages):
    print(f"Format {i}: {type(msg)} = {msg}")
