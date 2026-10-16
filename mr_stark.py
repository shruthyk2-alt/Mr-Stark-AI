from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.core.config import SETTINGS
from app.core.orchestrator import StarkOrchestrator
from app.personality.voice import StarkVoice
from app.tools.registry import TOOL_REGISTRY
from app.ui.main_window import StarkMainWindow, StartupSplash


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(SETTINGS.app_name)
    app.setApplicationVersion(SETTINGS.version)

    splash = StartupSplash()
    splash.show()
    splash.raise_()
    splash.activateWindow()

    app.processEvents()

    orchestrator = StarkOrchestrator()
    voice = StarkVoice(mode="focused")
    system_status = orchestrator.enumerate_status()

    window = StarkMainWindow()
    window.setWindowTitle(f"{SETTINGS.app_name} // {SETTINGS.mode}")
    window.show()

    splash.close()

    print(f"{SETTINGS.app_name} launched")
    print(f"Persona: {voice.greeting()}")
    print(f"System status: {system_status}")
    print(f"Tools available: {[tool.name for tool in TOOL_REGISTRY]}")

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
