from automation.backends.base import AgentBackend, AgentRunConfig
from automation.backends.codex import CodexBackend
from automation.backends.opencode import OpencodeBackend


def get_backend(name: str) -> AgentBackend:
    normalized = name.strip().lower()
    if normalized == "codex":
        return CodexBackend()
    if normalized == "opencode":
        return OpencodeBackend()
    raise ValueError(f"Unsupported backend '{name}'")

