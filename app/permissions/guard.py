from __future__ import annotations


class PermissionGuard:
    """Very lightweight permission gate for the desktop assistant."""

    def __init__(self, required_level: str = "safe") -> None:
        self.required_level = required_level

    def authorize(self, requested_action: str, user_level: str = "safe") -> bool:
        allowed = {
            "safe": {"safe", "controlled", "restricted"},
            "controlled": {"controlled", "restricted"},
            "restricted": {"restricted"},
        }
        return requested_action in {"read", "write", "execute", "deploy"} and user_level in allowed.get(self.required_level, {self.required_level})

    def explain(self, requested_action: str) -> str:
        return f"Permission check for '{requested_action}' is valid under the active policy."
