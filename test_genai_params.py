#!/usr/bin/env python3
import google.genai as genai
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found")
    exit(1)

# Initialize client
client = genai.Client(api_key=api_key)

print("Test 1: Check if system_instruction parameter exists")
try:
    # Try to call with system_instruction
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[{"role": "user", "parts": [{"text": "Hello"}]}],
        system_instruction="You are helpful"
    )
    print("SUCCESS: system_instruction parameter works")
except TypeError as e:
    if "system_instruction" in str(e):
        print(f"FAILED: {e}")
    else:
        print(f"OTHER ERROR: {e}")
except Exception as e:
    print(f"EXCEPTION: {e}")

print("\nTest 2: Try using Chat API with system instruction")
try:
    model = client.models.get_model("gemini-3.6-flash")
    print(f"Model available: {model.name}")
    
    # Try chat with system instruction
    chat = client.chats.create(
        model="gemini-3.6-flash",
        config={"system_instruction": "You are helpful"}
    )
    response = chat.send_message("Hello")
    print("SUCCESS: Chat API with system_instruction works")
except Exception as e:
    print(f"Chat API error: {type(e).__name__}: {e}")

print("\nTest 3: Check GenerateContentRequest parameters")
try:
    from google.genai.types import GenerateContentRequest
    import inspect
    sig = inspect.signature(GenerateContentRequest)
    print(f"GenerateContentRequest params: {list(sig.parameters.keys())}")
except Exception as e:
    print(f"Could not inspect GenerateContentRequest: {e}")
