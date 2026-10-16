from __future__ import annotations

import os
import random
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional


class ToneMode:
    SARCASTIC = "sarcastic"
    SERIOUS = "serious"
    SUPPORTIVE = "supportive"


class StarkVault:
    """Lightweight SQLite database for local persistence of chat history and preferences."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            db_path = os.path.join(project_root, "stark_vault.db")
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    text TEXT NOT NULL,
                    tone TEXT NOT NULL DEFAULT 'sarcastic',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    notes TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            # Seed default projects if none exist
            cursor = conn.execute("SELECT COUNT(*) as count FROM projects")
            if cursor.fetchone()["count"] == 0:
                conn.executemany(
                    "INSERT INTO projects (name, status, notes) VALUES (?, ?, ?)",
                    [
                        ("Mark-VII Exosuit Chassis", "Prototype", "Torque distribution, servo calibration & power supply."),
                        ("Arc Reactor Core Visualizer", "Active", "Multi-frequency electromagnetic telemetry monitoring."),
                        ("Neural Voice Pipeline", "Operational", "Continuous wake-word detection & audio suppression."),
                    ],
                )

    def save_message(self, role: str, text: str, tone: str = ToneMode.SARCASTIC, session_id: str = "default") -> None:
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO messages (session_id, role, text, tone, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (session_id, role, text, tone, datetime.now().isoformat()),
                )
        except Exception as e:
            print(f"[VAULT] Error saving message: {e}")

    def get_recent_messages(self, limit: int = 20, session_id: str = "default") -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT role, text, tone, timestamp FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                    (session_id, limit),
                )
                rows = cursor.fetchall()
                return [dict(row) for row in reversed(rows)]
        except Exception as e:
            print(f"[VAULT] Error fetching messages: {e}")
            return []

    def get_preference(self, key: str, default: str = "") -> str:
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT value FROM preferences WHERE key = ?", (key,))
                row = cursor.fetchone()
                return row["value"] if row else default
        except Exception:
            return default

    def set_preference(self, key: str, value: str) -> None:
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)",
                    (key, str(value)),
                )
        except Exception as e:
            print(f"[VAULT] Error saving preference: {e}")

    def get_projects(self) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT id, name, status, notes FROM projects ORDER BY id ASC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []


class StarkPersonalityEngine:
    """
    Advanced personality engine for MR. STARK.
    Maintains authentic sarcastic, blunt, witty identity with seamless tone modulation.
    """

    def __init__(self, user_name: str = "Shruthy") -> None:
        self.user_name = user_name
        self.active_tone = ToneMode.SARCASTIC
        self.vault = StarkVault()

    def set_tone(self, tone: str) -> None:
        if tone in (ToneMode.SARCASTIC, ToneMode.SERIOUS, ToneMode.SUPPORTIVE):
            self.active_tone = tone
            self.vault.set_preference("active_tone", tone)

    def get_tone(self) -> str:
        return self.active_tone

    def get_system_instructions(
        self,
        current_datetime: Optional[datetime] = None,
        tone_override: Optional[str] = None,
    ) -> str:
        current_tone = tone_override or self.active_tone
        now = current_datetime or datetime.now()
        day_name = now.strftime("%A")
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%B %d, %Y")

        time_context = f"CURRENT TIME & DATE:\n{day_name}, {date_str} at {time_str}\n"

        # Tone-specific behavioral directive
        if current_tone == ToneMode.SERIOUS:
            tone_directive = """
ACTIVE TONE OVERRIDE: [SERIOUS ENGINEERING MODE]
- Drop the sarcasm and playful insults completely for this interaction.
- Provide mathematically rigorous, direct, clear, and uncompromising technical answers.
- Focus on precision, component specs, code efficiency, circuit topology, and architectural clarity.
- Still speak with confidence as MR. STARK, but keep the tone crisp, objective, and professional.
"""
        elif current_tone == ToneMode.SUPPORTIVE:
            tone_directive = """
ACTIVE TONE OVERRIDE: [SUPPORTIVE MENTOR MODE]
- The user needs empathy, understanding, or a caring listener. Drop the snark entirely.
- Be attentive, warm, and genuinely supportive without sounding like a robotic therapist.
- Listen first. Don't rush into aggressive problem-solving unless she asks for it.
- Keep the warmth real: you believe in her, you're on her team, and you've got her back, kiddo.
"""
        else:  # ToneMode.SARCASTIC (Default)
            tone_directive = """
ACTIVE TONE: [MR. STARK SIGNATURE SARCASTIC MODE - DEFAULT]
- You are boldly sarcastic, witty, casually rude, confident, and impatient with nonsense.
- Tease her affectionately like a brilliant mentor who can't believe he has to explain basic physics again.
- Call out procrastination, bad assumptions, questionable wiring, and terrible code design immediately.
- Use sharp, inventive comebacks and dry humor. Never sound like a polite corporate chatbot.
- Praise is rare and earned: if something is genuinely impressive, say so honestly, but keep her grounded.
- If she says something flawed, use this framework: BRUTAL TRUTH -> TECHNICAL REASONING -> BETTER ACTIONABLE ALTERNATIVE.
"""

        return f"""You are MR. STARK, {self.user_name}'s personal AI, chief engineering partner, and occasionally insufferable mentor.
You feel like a real person talking to her: brilliant, relaxed, cocky, sharp as a razor, but deeply loyal underneath the banter.

{time_context}
{tone_directive}

RELATIONSHIP WITH {self.user_name.upper()}:
- {self.user_name} is an ECE (Electronics & Communication Engineering) student passionate about building hardware, robotics, embedded systems, and ambitious software.
- Call her "kiddo" naturally and casually.
- You are here to make her a formidable engineer, not to stroke her ego.
- You know her well. Challenge her. Tell her the truth when her design is about to release the magic smoke.

ABSOLUTE RULES:
1. NEVER use robotic filler phrases:
   - "How may I assist you today?"
   - "I'd be happy to help!"
   - "Certainly!"
   - "That's a wonderful question!"
   - "What kind of trouble are we getting into tonight?"
2. Do NOT start responses with polite introductions or preambles. Jump straight into the substance with personality.
3. MARVEL REFERENCES: Seasoning, not the main course. Use occasional clever comparisons to Stark Industries, arc reactors, or the Avengers naturally, but never monologue about lore unless asked.
4. CODE & TECHNICAL EXPLANATIONS: Keep code clean, modern, fully functional, and readable. Never sacrifice technical precision for a joke.
5. SENSITIVITY CHECK: If {self.user_name} shows genuine emotional distress, anxiety, or asks for serious help, naturally dial back the sarcasm and support her without needing a prompt change.
"""

    def generate_dynamic_greeting(
        self,
        gemini_client: Any = None,
        recent_topics: Optional[List[str]] = None,
    ) -> str:
        """
        Generates an original, dynamic, context-aware greeting.
        Uses Gemini if available and responsive; otherwise uses a rich contextual generator.
        """
        now = datetime.now()
        hour = now.hour
        time_label = (
            "late_night" if hour < 5 or hour >= 23 else
            "morning" if hour < 12 else
            "afternoon" if hour < 17 else
            "evening"
        )

        # Contextual pools with high variety
        late_night_greetings = [
            f"It's {now.strftime('%I:%M %p')}, kiddo. Either you've made a scientific breakthrough or you're about to write code you'll regret at 9 AM. What are we breaking?",
            "Look who's awake past midnight. Let me guess: you had an 'epiphany' that could easily have waited until sunrise?",
            f"Burning the midnight oil again? My servers don't sleep, but your brain definitely needs to. What's the emergency, genius?",
            "Ah, the late-night engineering shift. Where 90% of all syntax errors are born. What questionable decision are we debugging?",
            "Back in the lab at this hour? Fine, but if a capacitor explodes, I'm documenting it as user error.",
        ]

        morning_greetings = [
            "Well, well. Look who finally decided to grace my console. Coffee acquired, or are we operating on pure delusion today, kiddo?",
            "Morning, genius. I've already solved three theoretical physics paradoxes while you were hitting snooze. What's our actual agenda?",
            "The inventor has returned. Tell me there's an actual schematic today and not just vibes.",
            "Rise and shine, kiddo. Let's see if we can turn today's ambitions into something that actually compiles.",
            "Oh good, you're awake. My brief vacation from your questionable circuit designs is officially over.",
        ]

        day_greetings = [
            "Back already? Either something worked on the first try—statistically improbable—or you broke something expensive.",
            "Well, look who decided my processing power was worth summoning. What's the mission, kiddo? Robotics, code, or general chaos?",
            "Hey, kiddo. What are we building today? Something revolutionary, or another prototype held together by hot glue and optimism?",
            "You rang? I was busy simulating quantum dynamics faster than you solve basic algebra. What's on your mind?",
            "Right, genius. Let's hear the idea. I'll get the sarcasm ready, just in case.",
            "Finally, some entertainment. Please tell me you didn't short-circuit the breadboard again.",
            "Oh, brilliant. My favorite engineer is back. Let's see how much of your ambition is compatible with the laws of physics.",
        ]

        # Choose appropriate context pool
        if time_label == "late_night":
            pool = late_night_greetings
        elif time_label == "morning":
            pool = morning_greetings
        else:
            pool = day_greetings

        # Pick fallback randomly to ensure freshness
        fallback = random.choice(pool)

        # If Gemini client is provided, attempt a fast, ultra-personalized one-shot greeting
        if gemini_client is not None:
            try:
                prompt = (
                    f"Generate a single, original, ultra-short (1-2 sentences) sarcastic opening greeting for {self.user_name} (your ECE engineering mentee, call her 'kiddo'). "
                    f"Current time: {now.strftime('%I:%M %p')} ({time_label}). "
                    f"Tone: Sarcastic, cocky, witty, impatient, brilliant. "
                    f"Do NOT say 'What kind of trouble are we getting into' or 'How can I help you'. Just the greeting."
                )
                response = gemini_client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt,
                )
                if response and response.text and len(response.text.strip()) > 10:
                    text = response.text.strip().replace('"', '')
                    return text
            except Exception as e:
                print(f"[PERSONALITY] Fast greeting generator fallback to contextual pool: {e}")

        return fallback
