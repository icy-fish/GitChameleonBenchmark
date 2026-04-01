from __future__ import annotations

import copy
import json
import shlex
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from automation.agent_specs import AgentSpec, load_agent_spec
from automation.backends import get_backend
from automation.models import TaskBundle
from automation.protected_evaluator import evaluate_solutions
from automation.reporter import (
    archive_run_artifacts,
    build_run_setup,
    is_full_benchmark_run,
    summarize_results,
    update_project_history,
    write_agent_report,
    write_comparison_report,
)
from automation.solution_normalizer import extract_code
from automation.task_bundle_builder import build_task_bundles
from automation.workspace_builder import build_isolated_workspace


@dataclass
class OrchestratorConfig:
    benchmark_root: Path
    dataset_path: Path
    runs_root: Path
    workspace_root: Path
    include_visible_tests: bool
    workers: int


class BenchmarkOrchestrator:
    def __init__(self, config: OrchestratorConfig):
        self.config = config

    def create_run(self, run_id: str | None, agents: list[str], example_ids: list[str], limit: int | None) -> Path:
        resolved_run_id = run_id or datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")
        run_dir = self.config.runs_root / resolved_run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        config_payload = {
            "run_id": resolved_run_id,
            "agents": agents,
            "example_ids": example_ids,
            "limit": limit,
            "include_visible_tests": self.config.include_visible_tests,
            "workspace_root": str(self.config.workspace_root),
            "dataset_path": str(self.config.dataset_path),
        }
        (run_dir / "config.json").write_text(json.dumps(config_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return run_dir

    def prepare(self, run_dir: Path, agents: list[str], example_ids: list[str], limit: int | None) -> list[str]:
        bundles_dir = run_dir / "task_bundles"
        bundles = build_task_bundles(
            dataset_path=self.config.dataset_path,
            output_dir=bundles_dir,
            example_ids=example_ids or None,
            limit=limit,
            include_visible_tests=self.config.include_visible_tests,
        )
        for agent_name in agents:
            for bundle in bundles:
                build_isolated_workspace(
                    workspace_root=self.config.workspace_root,
                    run_id=run_dir.name,
                    agent_name=agent_name,
                    bundle=bundle,
                    include_visible_tests=self.config.include_visible_tests,
                )
        manifest = {
            "tasks": [bundle.example_id for bundle in bundles],
            "agents": agents,
        }
        (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return [bundle.example_id for bundle in bundles]

    def run_agent(
        self,
        run_dir: Path,
        agent_name: str,
        executable: str | None = None,
        args: list[str] | None = None,
        model: str | None = None,
        timeout_sec: int = 900,
        use_stdin_prompt: bool | None = None,
        container_image: str | None = None,
        container_workdir: str | None = None,
        container_network: str | None = None,
        container_args: list[str] | None = None,
    ) -> Path:
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        backend = get_backend(agent_name)
        agent_spec = load_agent_spec(self.config.benchmark_root, agent_name)
        config = backend.default_config()
        if agent_spec and agent_spec.executable and not executable:
            config.executable = agent_spec.executable
        if executable:
            config.executable = executable
        config.args = list(agent_spec.args) if agent_spec else []
        if args is not None:
            config.args = args
        config.timeout_sec = timeout_sec
        config.use_stdin_prompt = use_stdin_prompt if use_stdin_prompt is not None else (
            agent_spec.use_stdin_prompt if agent_spec else True
        )
        config.container_image = container_image or (agent_spec.image_name if agent_spec else None)
        config.container_workdir = container_workdir or (agent_spec.workspace_dir if agent_spec else "/workspace")
        config.container_network = container_network or (agent_spec.container_network if agent_spec else "none")
        config.container_args = container_args or []
        config.env = dict(agent_spec.env) if agent_spec else {}

        if config.container_image and agent_spec and config.container_image == agent_spec.image_name:
            self._ensure_agent_image(agent_spec)

        outputs_dir = run_dir / "outputs" / agent_name
        outputs_dir.mkdir(parents=True, exist_ok=True)
        raw_output_path = outputs_dir / "raw_outputs.jsonl"
        solutions_path = outputs_dir / "solutions.jsonl"

        task_examples = [str(example_id) for example_id in manifest["tasks"]]
        run_model = model or (agent_spec.default_model if agent_spec else "")
        if self.config.workers <= 1 or len(task_examples) <= 1:
            task_outputs = [
                self._run_agent_task(
                    backend=backend,
                    run_dir=run_dir,
                    agent_name=agent_name,
                    example_id=example_id,
                    base_config=config,
                    agent_spec=agent_spec,
                    model=run_model,
                )
                for example_id in task_examples
            ]
        else:
            max_workers = min(self.config.workers, len(task_examples))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                task_outputs = list(
                    executor.map(
                        lambda example_id: self._run_agent_task(
                            backend=backend,
                            run_dir=run_dir,
                            agent_name=agent_name,
                            example_id=example_id,
                            base_config=config,
                            agent_spec=agent_spec,
                            model=run_model,
                        ),
                        task_examples,
                    )
                )

        raw_records = [task_output["raw_record"] for task_output in task_outputs]
        solution_records = [task_output["solution_record"] for task_output in task_outputs]

        raw_output_path.write_text("".join(json.dumps(record) + "\n" for record in raw_records), encoding="utf-8")
        solutions_path.write_text("".join(json.dumps(record) + "\n" for record in solution_records), encoding="utf-8")
        return solutions_path

    def evaluate_agent(
        self,
        run_dir: Path,
        agent_name: str,
        docker_image: str | None = None,
        docker_tag: str | None = None,
    ) -> Path:
        solution_file = run_dir / "outputs" / agent_name / "solutions.jsonl"
        return evaluate_solutions(
            benchmark_root=self.config.benchmark_root,
            solution_file=solution_file,
            workers=self.config.workers,
            docker_image=docker_image,
            docker_tag=docker_tag,
        )

    def report(self, run_dir: Path, agents: list[str]) -> dict[str, dict]:
        report_dir = run_dir / "reports"
        summaries: dict[str, dict] = {}
        for agent_name in agents:
            eval_csv = run_dir / "outputs" / agent_name / "solutions_eval_results.csv"
            raw_output_path = run_dir / "outputs" / agent_name / "raw_outputs.jsonl"
            summary = summarize_results(self.config.dataset_path, eval_csv, raw_output_path)
            summary["run_setup"] = build_run_setup(self.config.benchmark_root, agent_name, raw_output_path)
            write_agent_report(report_dir, agent_name, summary)
            summaries[agent_name] = summary
        write_comparison_report(report_dir, summaries)
        if is_full_benchmark_run(run_dir, self.config.dataset_path):
            archived_run_dir = archive_run_artifacts(self.config.benchmark_root, run_dir)
            update_project_history(self.config.benchmark_root / "reports", archived_run_dir, summaries)
        return summaries

    def _load_task_bundle(self, run_dir: Path, example_id: str) -> TaskBundle:
        task_bundle_path = run_dir / "task_bundles" / str(example_id) / "task_bundle.json"
        payload = json.loads(task_bundle_path.read_text(encoding="utf-8"))
        return TaskBundle.from_dict(payload)

    def _run_agent_task(
        self,
        backend,
        run_dir: Path,
        agent_name: str,
        example_id: str,
        base_config,
        agent_spec: AgentSpec | None,
        model: str,
    ) -> dict[str, dict]:
        workspace = self.config.workspace_root / run_dir.name / agent_name / example_id
        bundle = self._load_task_bundle(run_dir, example_id)
        task_config = self._build_task_config(
            base_config=base_config,
            agent_name=agent_name,
            bundle=bundle,
            model=model,
            agent_spec=agent_spec,
        )
        result = backend.run(workspace=workspace, config=task_config)
        answer = extract_code(result.solution_text or result.stdout)
        raw_record = {
            "example_id": example_id,
            "agent": agent_name,
            "command": result.command,
            "exit_code": result.exit_code,
            "timed_out": result.timed_out,
            "started_at": result.started_at,
            "completed_at": result.completed_at,
            "duration_sec": result.duration_sec,
            "metrics": result.metrics,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "combined_output": result.combined_output,
            "solution_text": result.solution_text,
            "workspace": str(workspace),
            "container_image": task_config.container_image,
            "answer_source": "result_file" if result.solution_text else "stdout",
        }
        solution_record = {
            "example_id": example_id,
            "answer": answer,
        }
        (workspace / "agent_stdout.txt").write_text(result.stdout, encoding="utf-8")
        (workspace / "agent_stderr.txt").write_text(result.stderr, encoding="utf-8")
        log_header = self._build_agent_log_header(result.command)
        (workspace / "agent_log.txt").write_text(log_header + result.combined_output, encoding="utf-8")
        return {
            "raw_record": raw_record,
            "solution_record": solution_record,
        }

    def _build_task_config(
        self,
        base_config,
        agent_name: str,
        bundle: TaskBundle,
        model: str,
        agent_spec: AgentSpec | None,
    ):
        task_config = copy.deepcopy(base_config)
        venv_host_path = self.config.benchmark_root / ".dataset_venvs" / bundle.venv_name()
        if not venv_host_path.is_dir():
            raise FileNotFoundError(f"Missing task venv for example {bundle.example_id}: {venv_host_path}")

        inner_workspace = Path(task_config.container_workdir)
        container_venv_path = inner_workspace / ".dataset_venvs" / bundle.venv_name()
        task_config.extra_mounts = [(str(venv_host_path.resolve()), str(container_venv_path))]
        if agent_spec is not None and agent_spec.agent_dir.is_dir():
            task_config.extra_mounts.append((str(agent_spec.agent_dir.resolve()), "/agent"))
        if agent_spec is not None and agent_spec.result_file_template:
            result_file = agent_spec.result_file_template.format(example_id=bundle.example_id)
        else:
            result_file = bundle.result_filename()
        task_config.result_file = result_file
        task_config.env.update(
            {
                "GC_SAMPLE_PATH": str(inner_workspace / bundle.sample_filename()),
                "GC_RESULT_PATH": str(inner_workspace / result_file),
                "GC_TASK_VENV": str(container_venv_path),
                "GC_AGENT_DIR": "/agent",
                "PATH": (
                    f"{container_venv_path / 'bin'}:"
                    "/root/.opencode/bin:/root/.local/bin:"
                    "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
                ),
                "VIRTUAL_ENV": str(container_venv_path),
            }
        )
        if model:
            task_config.env["GC_AGENT_MODEL"] = model
        task_config.format_vars = {
            "agent_name": agent_name,
            "example_id": bundle.example_id,
            "model": model,
            "sample_path": str(inner_workspace / bundle.sample_filename()),
            "result_file": result_file,
            "result_path": str(inner_workspace / result_file),
            "task_venv": str(container_venv_path),
            "venv_name": bundle.venv_name(),
        }
        if agent_spec is not None and agent_spec.prompt_template:
            task_config.format_vars["prompt"] = agent_spec.prompt_template.format(**task_config.format_vars)
        return task_config

    def _ensure_agent_image(self, agent_spec: AgentSpec) -> None:
        if not agent_spec.image_name:
            return
        inspect_result = subprocess.run(
            ["docker", "image", "inspect", agent_spec.image_name],
            capture_output=True,
            text=True,
        )
        if inspect_result.returncode == 0:
            return
        if not agent_spec.dockerfile_path.is_file():
            raise FileNotFoundError(f"Missing Dockerfile for agent '{agent_spec.name}': {agent_spec.dockerfile_path}")
        subprocess.run(
            ["docker", "build", "-t", agent_spec.image_name, str(agent_spec.agent_dir)],
            cwd=self.config.benchmark_root,
            check=True,
        )

    def _build_agent_log_header(self, command: list[str]) -> str:
        lines = [
            "# Agent Command",
            shlex.join(command),
            "",
            "# Agent Output",
            "",
        ]
        return "\n".join(lines)
