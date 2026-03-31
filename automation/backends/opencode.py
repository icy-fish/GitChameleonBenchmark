from automation.backends.base import AgentBackend
import json
from typing import Any


class OpencodeBackend(AgentBackend):
    name = "opencode"
    default_executable = "opencode"

    _PROMPT_TOKEN_KEYS = ("prompt_tokens", "promptTokens", "input_tokens", "inputTokens")
    _COMPLETION_TOKEN_KEYS = ("completion_tokens", "completionTokens", "output_tokens", "outputTokens")
    _TOTAL_TOKEN_KEYS = ("total_tokens", "totalTokens", "tokens", "tokenCount")

    def extract_metrics(
        self,
        *,
        stdout: str,
        stderr: str,
        combined_output: str,
        exit_code: int,
        timed_out: bool,
    ) -> dict[str, Any]:
        usage = self._extract_usage_from_jsonl(combined_output)
        if not usage:
            return {}
        return {
            "token_usage": usage,
        }

    def _extract_usage_from_jsonl(self, output: str) -> dict[str, int] | None:
        best_candidate: dict[str, int] | None = None
        for line in output.splitlines():
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            for candidate in self._iter_usage_candidates(payload):
                best_candidate = self._select_better_candidate(best_candidate, candidate)
        return best_candidate

    def _iter_usage_candidates(self, value: Any):
        if isinstance(value, dict):
            normalized = self._normalize_usage_dict(value)
            if normalized:
                yield normalized
            for nested in value.values():
                yield from self._iter_usage_candidates(nested)
            return
        if isinstance(value, list):
            for item in value:
                yield from self._iter_usage_candidates(item)

    def _normalize_usage_dict(self, value: dict[str, Any]) -> dict[str, int] | None:
        prompt_tokens = self._coerce_first_int(value, self._PROMPT_TOKEN_KEYS)
        completion_tokens = self._coerce_first_int(value, self._COMPLETION_TOKEN_KEYS)
        total_tokens = self._coerce_first_int(value, self._TOTAL_TOKEN_KEYS)
        if prompt_tokens is None and completion_tokens is not None:
            prompt_tokens = 0
        if completion_tokens is None and prompt_tokens is not None:
            completion_tokens = 0
        if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
            total_tokens = prompt_tokens + completion_tokens
        if total_tokens is None:
            return None
        normalized = {"total_tokens": total_tokens}
        if prompt_tokens is not None:
            normalized["prompt_tokens"] = prompt_tokens
        if completion_tokens is not None:
            normalized["completion_tokens"] = completion_tokens
        return normalized

    def _coerce_first_int(self, value: dict[str, Any], keys: tuple[str, ...]) -> int | None:
        for key in keys:
            if key not in value:
                continue
            raw = value[key]
            if isinstance(raw, bool):
                continue
            if isinstance(raw, int):
                return raw
            if isinstance(raw, float):
                return int(raw)
            if isinstance(raw, str):
                try:
                    return int(raw)
                except ValueError:
                    continue
        return None

    def _select_better_candidate(
        self,
        current: dict[str, int] | None,
        candidate: dict[str, int],
    ) -> dict[str, int]:
        if current is None:
            return candidate
        current_total = current.get("total_tokens", -1)
        candidate_total = candidate.get("total_tokens", -1)
        if candidate_total >= current_total:
            return candidate
        return current
