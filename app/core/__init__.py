"""Core orchestration for MR. STARK."""

from .config import SETTINGS
from .orchestrator import StarkOrchestrator

__all__ = ["SETTINGS", "StarkOrchestrator"]
