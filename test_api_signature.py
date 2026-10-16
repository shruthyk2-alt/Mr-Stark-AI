#!/usr/bin/env python3
import google.genai as genai
import os
from dotenv import load_dotenv
import inspect

# Load API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env")
    exit(1)

# Initialize client
client = genai.Client(api_key=api_key)

# Check the models attribute
print("Client.models type:", type(client.models))
print("Client.models methods:", [x for x in dir(client.models) if not x.startswith('_')])

# Try to get the generate_content method
print("\n" + "="*60)
print("Inspecting generate_content:")
print("="*60)

try:
    sig = inspect.signature(client.models.generate_content)
    print('Signature:', sig)
    print('\nParameters:')
    for param_name, param in sig.parameters.items():
        annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type"
        default = param.default if param.default != inspect.Parameter.empty else "REQUIRED"
        print(f'  {param_name}: {annotation} = {default}')
except Exception as e:
    print(f"Error getting signature: {e}")

# Check available types
print("\n" + "="*60)
print("Available types in google.genai.types:")
print("="*60)
from google.genai import types
for name in dir(types):
    if not name.startswith('_'):
        print(f"  - {name}")
