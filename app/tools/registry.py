from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    category: str
    description: str


TOOL_REGISTRY = [
    ToolDefinition("System Scan", "ops", "Survey the current environment and hardware posture."),
    ToolDefinition("Mission Planner", "ops", "Draft a prioritized action plan for the next cycle."),
    ToolDefinition("Permission Audit", "security", "Review resource access and control surfaces."),
    ToolDefinition("Persona Sync", "intel", "Align communication style with the active working mode."),
]
