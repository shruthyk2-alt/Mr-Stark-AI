from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Any

from app.personality.engine import StarkPersonalityEngine, ToneMode, StarkVault


class StarkVoice:
    """
    Defines the operational tone and phrasing style for MR. STARK.
    Now backed by the advanced StarkPersonalityEngine for dynamic sarcasm,
    tone switching, and persistent session memory.
    """

    def __init__(self, mode: str = "focused", user_name: str = "Shruthy") -> None:
        self.mode = mode
        self.user_name = user_name
        self.engine = StarkPersonalityEngine(user_name=user_name)

    def greeting(self, gemini_client: Any = None) -> str:
        """Returns an authentic, dynamic, non-repetitive greeting."""
        return self.engine.generate_dynamic_greeting(gemini_client=gemini_client)

    def status_message(self) -> str:
        return "All systems online. Directives remain aligned with mission priorities."

    def set_tone(self, tone: str) -> None:
        """Switch between ToneMode.SARCASTIC, ToneMode.SERIOUS, and ToneMode.SUPPORTIVE."""
        self.engine.set_tone(tone)

    def get_tone(self) -> str:
        return self.engine.get_tone()

    def system_instructions(
        self,
        current_datetime: Optional[datetime] = None,
        tone_override: Optional[str] = None,
    ) -> str:
        """
        Comprehensive system instructions for MR. STARK's active personality.
        """
        return self.engine.get_system_instructions(
            current_datetime=current_datetime,
            tone_override=tone_override,
        )

