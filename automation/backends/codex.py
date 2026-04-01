from __future__ import annotations

import json
from typing import Any

from automation.backends.base import AgentBackend


class CodexBackend(AgentBackend):
    name = "codex"
    default_executable = "codex"

    def extract_metrics(
        self,
        *,
        stdout: str,
        stderr: str,
        combined_output: str,
        exit_code: int,
        timed_out: bool,
    ) -> dict[str, Any]:
        token_usage = self._extract_token_usage(combined_output)
        return {"token_usage": token_usage} if token_usage else {}

    def _extract_token_usage(self, output: str) -> dict[str, int] | None:
        for line in output.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") != "turn.completed":
                continue
            usage = event.get("usage")
            if not isinstance(usage, dict):
                continue
            prompt_tokens = int(usage.get("input_tokens", 0))
            completion_tokens = int(usage.get("output_tokens", 0))
            return {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            }
        return None
