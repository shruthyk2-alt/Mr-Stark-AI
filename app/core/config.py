from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    app_name: str = "MR. STARK"
    version: str = "1.0.0"
    mode: str = "Autonomous desktop intelligence"
    security_level: str = "Tier-1"
    status: str = "Operational"


SETTINGS = AppSettings()
