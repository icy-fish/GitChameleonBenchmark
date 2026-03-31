from __future__ import annotations

from pathlib import Path

from automation.models import TaskBundle

def build_isolated_workspace(
    workspace_root: Path,
    run_id: str,
    agent_name: str,
    bundle: TaskBundle,
    include_visible_tests: bool,
) -> Path:
    task_dir = workspace_root / run_id / agent_name / bundle.example_id
    task_dir.mkdir(parents=True, exist_ok=True)
    _reset_task_dir(task_dir, bundle)

    (task_dir / bundle.sample_filename()).write_text(bundle.render_sample(), encoding="utf-8")

    validate_workspace(task_dir)
    return task_dir


def _reset_task_dir(task_dir: Path, bundle: TaskBundle) -> None:
    removable_patterns = (
        "sample_*.py",
        "result_*.py",
        "agent_log.txt",
        "agent_stdout.txt",
        "agent_stderr.txt",
        "metadata.json",
        "prompt.md",
        "requirements.txt",
        "starting_code.py",
        "task_bundle.json",
    )
    for pattern in removable_patterns:
        for path in task_dir.glob(pattern):
            if path.is_file():
                path.unlink()
    venv_mount_dir = task_dir / ".dataset_venvs" / bundle.venv_name()
    venv_mount_dir.mkdir(parents=True, exist_ok=True)


def validate_workspace(task_dir: Path) -> None:
    file_names = {path.name for path in task_dir.iterdir() if path.is_file()}
    allowed_dynamic = {name for name in file_names if name.startswith("sample_") and name.endswith(".py")}
    unexpected = sorted(file_names - allowed_dynamic)
    if unexpected:
        raise RuntimeError(f"Unexpected files present in isolated workspace {task_dir}: {unexpected}")
    forbidden_fragments = ("hidden_tests", "ground_truth_solutions", "solution")
    for path in task_dir.rglob("*"):
        if any(fragment in path.name for fragment in forbidden_fragments):
            raise RuntimeError(f"Forbidden artifact leaked into workspace: {path}")
