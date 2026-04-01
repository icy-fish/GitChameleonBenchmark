from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class AgentRunConfig:
    executable: str
    args: list[str] = field(default_factory=list)
    timeout_sec: int = 900
    env: dict[str, str] = field(default_factory=dict)
    use_stdin_prompt: bool = True
    container_image: str | None = None
    container_workdir: str = "/workspace"
    container_network: str = "none"
    container_args: list[str] = field(default_factory=list)
    extra_mounts: list[tuple[str, str]] = field(default_factory=list)
    format_vars: dict[str, str] = field(default_factory=dict)
    result_file: str | None = None


@dataclass
class AgentRunResult:
    stdout: str
    stderr: str
    combined_output: str
    exit_code: int
    timed_out: bool
    command: list[str]
    started_at: str
    completed_at: str
    duration_sec: float
    metrics: dict[str, Any] = field(default_factory=dict)
    solution_text: str | None = None


class AgentBackend:
    name = "agent"
    default_executable = ""

    def default_config(self) -> AgentRunConfig:
        return AgentRunConfig(executable=self.default_executable)

    def run(
        self,
        workspace: Path,
        config: AgentRunConfig,
    ) -> AgentRunResult:
        execution_workspace = workspace
        temp_workspace: tempfile.TemporaryDirectory[str] | None = None
        if config.container_image:
            temp_workspace = tempfile.TemporaryDirectory(prefix=f"{self.name}_workspace_", ignore_cleanup_errors=True)
            execution_workspace = Path(temp_workspace.name)
            shutil.copytree(workspace, execution_workspace, dirs_exist_ok=True)

        prompt_path = execution_workspace / "prompt.md"
        prompt_input = prompt_path.read_text(encoding="utf-8") if config.use_stdin_prompt and prompt_path.is_file() else None
        command, env = self._build_command_and_env(workspace, execution_workspace, config)
        started_at = datetime.now(timezone.utc)
        started_monotonic = time.monotonic()
        try:
            proc = subprocess.run(
                command,
                cwd=execution_workspace,
                input=prompt_input,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=config.timeout_sec,
                env=env,
            )
            solution_text = self._read_solution_text(execution_workspace, config)
            completed_at = datetime.now(timezone.utc)
            duration_sec = time.monotonic() - started_monotonic
            metrics = self.extract_metrics(
                stdout=proc.stdout,
                stderr="",
                combined_output=proc.stdout,
                exit_code=proc.returncode,
                timed_out=False,
            )
            return AgentRunResult(
                stdout=proc.stdout,
                stderr="",
                combined_output=proc.stdout,
                exit_code=proc.returncode,
                timed_out=False,
                command=command,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_sec=duration_sec,
                metrics=metrics,
                solution_text=solution_text,
            )
        except subprocess.TimeoutExpired as exc:
            combined_output = self._coerce_text(exc.stdout)
            completed_at = datetime.now(timezone.utc)
            duration_sec = time.monotonic() - started_monotonic
            return AgentRunResult(
                stdout=combined_output,
                stderr="",
                combined_output=combined_output,
                exit_code=124,
                timed_out=True,
                command=command,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_sec=duration_sec,
                metrics=self.extract_metrics(
                    stdout=combined_output,
                    stderr="",
                    combined_output=combined_output,
                    exit_code=124,
                    timed_out=True,
                ),
                solution_text=self._read_solution_text(execution_workspace, config),
            )
        except FileNotFoundError as exc:
            message = str(exc)
            completed_at = datetime.now(timezone.utc)
            duration_sec = time.monotonic() - started_monotonic
            return AgentRunResult(
                stdout="",
                stderr=message,
                combined_output=message,
                exit_code=127,
                timed_out=False,
                command=command,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_sec=duration_sec,
                metrics=self.extract_metrics(
                    stdout="",
                    stderr=message,
                    combined_output=message,
                    exit_code=127,
                    timed_out=False,
                ),
                solution_text=self._read_solution_text(execution_workspace, config),
            )
        finally:
            if temp_workspace is not None:
                try:
                    temp_workspace.cleanup()
                except PermissionError:
                    pass

    def _build_command_and_env(
        self,
        source_workspace: Path,
        execution_workspace: Path,
        config: AgentRunConfig,
    ) -> tuple[list[str], dict[str, str]]:
        if config.container_image:
            return self._build_container_command_and_env(source_workspace, execution_workspace, config)
        return self._build_host_command_and_env(execution_workspace, config)

    def _build_host_command_and_env(self, workspace: Path, config: AgentRunConfig) -> tuple[list[str], dict[str, str]]:
        prompt_path = workspace / "prompt.md"
        command = [config.executable] + [self._format_arg(arg, workspace, config) for arg in config.args]
        env = os.environ.copy()
        env.update(config.env)
        env.update(
            {
                "GC_PROMPT_PATH": str(prompt_path),
                "GC_TASK_BUNDLE_PATH": str(workspace / "task_bundle.json"),
                "GC_STARTING_CODE_PATH": str(workspace / "starting_code.py"),
                "GC_REQUIREMENTS_PATH": str(workspace / "requirements.txt"),
                "GC_WORKSPACE": str(workspace),
            }
        )
        return command, env

    def _build_container_command_and_env(
        self,
        source_workspace: Path,
        execution_workspace: Path,
        config: AgentRunConfig,
    ) -> tuple[list[str], dict[str, str]]:
        inner_workspace = Path(config.container_workdir)
        inner_prompt = inner_workspace / "prompt.md"
        inner_task_bundle = inner_workspace / "task_bundle.json"
        inner_starting_code = inner_workspace / "starting_code.py"
        inner_requirements = inner_workspace / "requirements.txt"

        inner_command = [
            self._format_arg(
                arg,
                execution_workspace,
                config,
                workspace_override=inner_workspace,
                prompt_override=inner_prompt,
                task_bundle_override=inner_task_bundle,
                starting_code_override=inner_starting_code,
                requirements_override=inner_requirements,
            )
            for arg in config.args
        ]

        command = [
            "docker",
            "run",
            "--rm",
            "-i",
            "-v",
            f"{execution_workspace.resolve()}:{config.container_workdir}",
            "-w",
            config.container_workdir,
            "--network",
            config.container_network,
            "--entrypoint",
            config.executable,
        ]
        for host_path, container_path in config.extra_mounts:
            command.extend(["-v", f"{host_path}:{container_path}"])
        for key, value in config.env.items():
            command.extend(["-e", f"{key}={value}"])
        command.extend(
            [
                "-e",
                f"GC_PROMPT_PATH={inner_prompt}",
                "-e",
                f"GC_TASK_BUNDLE_PATH={inner_task_bundle}",
                "-e",
                f"GC_STARTING_CODE_PATH={inner_starting_code}",
                "-e",
                f"GC_REQUIREMENTS_PATH={inner_requirements}",
                "-e",
                f"GC_WORKSPACE={inner_workspace}",
            ]
        )
        command.extend(config.container_args)
        command.append(config.container_image)
        command.extend(inner_command)
        return command, os.environ.copy()

    def _format_arg(
        self,
        arg: str,
        workspace: Path,
        config: AgentRunConfig,
        workspace_override: Path | None = None,
        prompt_override: Path | None = None,
        task_bundle_override: Path | None = None,
        starting_code_override: Path | None = None,
        requirements_override: Path | None = None,
    ) -> str:
        final_workspace = workspace_override or workspace
        replacements = {
            "workspace": str(final_workspace),
            "prompt_path": str(prompt_override or (final_workspace / "prompt.md")),
            "task_bundle_path": str(task_bundle_override or (final_workspace / "task_bundle.json")),
            "starting_code_path": str(starting_code_override or (final_workspace / "starting_code.py")),
            "requirements_path": str(requirements_override or (final_workspace / "requirements.txt")),
        }
        replacements.update(config.format_vars)
        return arg.format(**replacements)

    def _read_solution_text(self, workspace: Path, config: AgentRunConfig) -> str | None:
        if not config.result_file:
            return None
        result_path = workspace / config.result_file
        if not result_path.is_file():
            return None
        return result_path.read_text(encoding="utf-8")

    def _coerce_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value)

    def extract_metrics(
        self,
        *,
        stdout: str,
        stderr: str,
        combined_output: str,
        exit_code: int,
        timed_out: bool,
    ) -> dict[str, Any]:
        return {}
