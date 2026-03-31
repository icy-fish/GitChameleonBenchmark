from automation.backends.base import AgentBackend


class CodexBackend(AgentBackend):
    name = "codex"
    default_executable = "codex"

