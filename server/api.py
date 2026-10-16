from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
import psutil
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import google.genai as genai
from app.personality.engine import StarkPersonalityEngine, ToneMode, StarkVault

load_dotenv(os.path.join(project_root, ".env"))

app = FastAPI(title="MR. STARK Intelligence Gateway", version="2.0.0")

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
api_key = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=api_key) if api_key else None
engine = StarkPersonalityEngine(user_name="Shruthy")
vault = StarkVault()

conversation_history: List[Dict[str, Any]] = []


class ChatRequest(BaseModel):
    message: str
    voice_enabled: bool = False
    context_tags: Optional[List[str]] = None
    user_tone: Optional[str] = None


@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    return {
        "status": "online",
        "app_name": "MR. STARK // COMMAND NODE",
        "version": "2.0.0",
        "gemini_connected": gemini_client is not None,
        "vault_db": "stark_vault.db",
        "total_messages_persisted": len(vault.get_recent_messages(limit=500)),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/greeting")
def get_dynamic_greeting() -> Dict[str, Any]:
    greeting_text = engine.generate_dynamic_greeting(gemini_client=gemini_client)
    vault.save_message("model", greeting_text, tone=engine.get_tone())
    return {
        "greeting": greeting_text,
        "timestamp": datetime.now().strftime("%I:%M %p"),
        "persona": engine.get_tone(),
    }


@app.post("/api/chat")
def handle_chat(req: ChatRequest) -> Dict[str, Any]:
    prompt = req.message.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Empty prompt")

    # Persist user prompt
    vault.save_message("user", prompt, tone=engine.get_tone())
    conversation_history.append({"role": "user", "parts": [{"text": prompt}]})

    if gemini_client is None:
        fallback = "Gemini API key is not configured in .env. Check your configuration, kiddo."
        return {
            "reply": fallback,
            "timestamp": datetime.now().strftime("%I:%M %p"),
            "model": "offline-fallback",
        }

    try:
        recent_history = conversation_history[-10:]
        system_instruction = engine.get_system_instructions(current_datetime=datetime.now())

        config = genai.types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.85,
        )

        # Attempt with active model
        try:
            resp = gemini_client.models.generate_content(
                model="gemini-3.6-flash",
                contents=recent_history,
                config=config,
            )
        except Exception:
            resp = gemini_client.models.generate_content(
                model="gemini-3.8-flash",
                contents=recent_history,
                config=config,
            )

        answer = resp.text.strip() if (resp and resp.text) else "No response generated."
        vault.save_message("model", answer, tone=engine.get_tone())
        conversation_history.append({"role": "model", "parts": [{"text": answer}]})

        # Calculate mock suit stats responding to activity
        return {
            "reply": answer,
            "response": answer,
            "detected_state": engine.get_tone(),
            "timestamp": datetime.now().strftime("%I:%M %p"),
            "model": "gemini-3.6-flash",
            "telemetry": get_telemetry(),
        }
    except Exception as e:
        error_msg = f"System fault while reaching AI neural core: {e}"
        return {
            "reply": error_msg,
            "response": error_msg,
            "detected_state": "system fault",
            "timestamp": datetime.now().strftime("%I:%M %p"),
            "error": True,
        }


@app.get("/api/telemetry")
def get_telemetry() -> Dict[str, Any]:
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_percent": round(cpu, 1),
        "ram_percent": round(mem.percent, 1),
        "ram_used_gb": round(mem.used / (1024**3), 1),
        "ram_total_gb": round(mem.total / (1024**3), 1),
        "disk_percent": round(disk.percent, 1),
        "suit_stats": {
            "armor_integrity": 98,
            "power_level": 87,
            "temperature_c": 32,
            "battery_pct": 76,
        },
        "stream_states": {
            "audio_input": True,
            "processing_gemini": False,
            "knowledge_base": True,
            "memory_retrieval": True,
            "response_generation": True,
        },
    }


@app.get("/api/vault/projects")
def get_vault_projects() -> List[Dict[str, Any]]:
    return vault.get_projects()


@app.get("/api/vault/messages")
def get_vault_messages(limit: int = 30) -> List[Dict[str, Any]]:
    return vault.get_recent_messages(limit=limit)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.api:app", host="127.0.0.1", port=8000, reload=True)
