from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Mission:
    title: str
    status: str = "Queued"
    details: str = "Awaiting dispatch"


@dataclass
class StarkOrchestrator:
    missions: List[Mission] = field(default_factory=lambda: [
        Mission("Launch systems", "Ready", "Core diagnostics complete."),
        Mission("Assess security posture", "Monitoring", "Permissions verified."),
        Mission("Coordinate operations", "Queued", "Awaiting instruction."),
    ])

    def enumerate_status(self) -> list[str]:
        return [f"{mission.title}: {mission.status}" for mission in self.missions]

    def add_mission(self, title: str, status: str = "Queued", details: str = "Awaiting dispatch") -> None:
        self.missions.append(Mission(title=title, status=status, details=details))
