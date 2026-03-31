from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AgentSpec:
    name: str
    agent_dir: Path
    image_name: str | None = None
    default_model: str | None = None
    workspace_dir: str = "/app"
    container_network: str = "bridge"
    executable: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    use_stdin_prompt: bool = True
    result_file_template: str | None = None
    prompt_template: str | None = None

    @property
    def dockerfile_path(self) -> Path:
        return self.agent_dir / "Dockerfile"


def load_agent_spec(benchmark_root: Path, agent_name: str) -> AgentSpec | None:
    agent_dir = benchmark_root / "agents" / agent_name
    config_path = agent_dir / "agent.json"
    if not config_path.is_file():
        config_path = agent_dir / "config.json"
    if not config_path.is_file():
        return None

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    prompt_file_name = raw.get("prompt_file", "prompt.txt")
    prompt_path = agent_dir / prompt_file_name
    command = raw.get("command") or []
    executable = raw.get("executable")
    args = list(raw.get("args") or [])
    if command:
        executable = executable or command[0]
        args = args or command[1:]
    return AgentSpec(
        name=agent_name,
        agent_dir=agent_dir,
        image_name=raw.get("image_name"),
        default_model=raw.get("default_model") or raw.get("env", {}).get("GC_AGENT_MODEL"),
        workspace_dir=raw.get("workspace_dir") or "/app",
        container_network=raw.get("container_network") or "bridge",
        executable=executable,
        args=args,
        env=raw.get("env") or {},
        use_stdin_prompt=bool(raw.get("use_stdin_prompt", True)),
        result_file_template=raw.get("result_file_template"),
        prompt_template=prompt_path.read_text(encoding="utf-8") if prompt_path.is_file() else None,
    )
