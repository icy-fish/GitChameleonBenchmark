from __future__ import annotations

import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from automation.agent_specs import load_agent_spec
from automation.backends.opencode import OpencodeBackend


def _load_dataset_index(dataset_path: Path) -> dict[str, dict]:
    with dataset_path.open("r", encoding="utf-8") as handle:
        return {str(row["example_id"]): row for row in (json.loads(line) for line in handle if line.strip())}


def _dataset_size(dataset_path: Path) -> int:
    with dataset_path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _path_relative_to_reports(path_str: str) -> str:
    path = Path(path_str)
    if path.parts and path.parts[0] == "reports":
        return str(Path(*path.parts[1:]))
    return str(path)


def _agent_version_from_spec(agent_name: str, image_name: str | None) -> str:
    if image_name and ":" in image_name:
        return image_name.rsplit(":", 1)[1]
    if image_name:
        return image_name
    return agent_name


def _model_from_raw_records(raw_records: list[dict]) -> str | None:
    for record in raw_records:
        command = record.get("command") or []
        if not isinstance(command, list):
            continue
        for index, arg in enumerate(command[:-1]):
            if arg in {"-m", "--model"}:
                candidate = command[index + 1]
                if isinstance(candidate, str) and candidate.strip():
                    return candidate
    return None


def build_run_setup(benchmark_root: Path, agent_name: str, raw_output_path: Path | None) -> dict[str, str]:
    agent_spec = load_agent_spec(benchmark_root, agent_name)
    raw_records = _load_raw_run_records(raw_output_path)
    model_name = _model_from_raw_records(raw_records) or (agent_spec.default_model if agent_spec else "") or "unknown"
    image_name = agent_spec.image_name if agent_spec else None
    return {
        "identifier": f"{agent_name}:{model_name}",
        "agent_name": agent_name,
        "agent_version": _agent_version_from_spec(agent_name, image_name),
        "model_name": model_name,
        "initial_prompt": agent_spec.prompt_template.strip() if agent_spec and agent_spec.prompt_template else "",
    }


def _load_raw_run_records(raw_output_path: Path | None) -> list[dict]:
    if raw_output_path is None or not raw_output_path.is_file():
        return []
    with raw_output_path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _summarize_runtime_metrics(raw_records: list[dict]) -> dict:
    durations = [float(record["duration_sec"]) for record in raw_records if record.get("duration_sec") is not None]
    opencode_backend = OpencodeBackend()
    token_usage_records: list[dict] = []
    for record in raw_records:
        metrics = record.get("metrics")
        if isinstance(metrics, dict) and isinstance(metrics.get("token_usage"), dict):
            token_usage_records.append(metrics["token_usage"])
            continue
        if record.get("agent") != "opencode":
            continue
        reparsed_metrics = opencode_backend.extract_metrics(
            stdout=record.get("stdout", ""),
            stderr=record.get("stderr", ""),
            combined_output=record.get("combined_output", ""),
            exit_code=int(record.get("exit_code", 0)),
            timed_out=bool(record.get("timed_out", False)),
        )
        token_usage = reparsed_metrics.get("token_usage")
        if isinstance(token_usage, dict):
            token_usage_records.append(token_usage)
    total_prompt_tokens = sum(int(usage.get("prompt_tokens", 0)) for usage in token_usage_records)
    total_completion_tokens = sum(int(usage.get("completion_tokens", 0)) for usage in token_usage_records)
    total_tokens = sum(int(usage.get("total_tokens", 0)) for usage in token_usage_records)
    return {
        "runtime": {
            "count": len(durations),
            "total_seconds": sum(durations),
            "average_seconds": sum(durations) / len(durations) if durations else 0.0,
        },
        "token_usage": {
            "count": len(token_usage_records),
            "total_tokens": total_tokens,
            "average_tokens": total_tokens / len(token_usage_records) if token_usage_records else 0.0,
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
        },
    }


def summarize_results(dataset_path: Path, eval_csv: Path, raw_output_path: Path | None = None) -> dict:
    dataset_index = _load_dataset_index(dataset_path)
    rows: list[dict[str, str]] = []
    with eval_csv.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows.extend(reader)
    raw_records = _load_raw_run_records(raw_output_path)

    total = len(rows)
    hidden_passed = sum(row["passed"] == "True" for row in rows)
    hidden_compiled = sum(row["compiled"] == "True" for row in rows)
    visible_passed = sum(row["passed_manual"] == "True" for row in rows)
    visible_compiled = sum(row["compiled_manual"] == "True" for row in rows)

    library_breakdown: Counter[str] = Counter()
    library_passed: Counter[str] = Counter()
    for row in rows:
        sample = dataset_index[str(row["example_id"])]
        library = sample["library"]
        library_breakdown[library] += 1
        if row["passed"] == "True":
            library_passed[library] += 1

    return {
        "total": total,
        "hidden_passed": hidden_passed,
        "hidden_compiled": hidden_compiled,
        "visible_passed": visible_passed,
        "visible_compiled": visible_compiled,
        "hidden_pass_rate": hidden_passed / total if total else 0.0,
        "visible_pass_rate": visible_passed / total if total else 0.0,
        "library_breakdown": {
            library: {
                "total": library_breakdown[library],
                "passed": library_passed[library],
                "pass_rate": library_passed[library] / library_breakdown[library] if library_breakdown[library] else 0.0,
            }
            for library in sorted(library_breakdown)
        },
        "metrics": _summarize_runtime_metrics(raw_records),
    }


def write_agent_report(report_dir: Path, agent_name: str, summary: dict) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    summary_path = report_dir / f"{agent_name}_summary.json"
    markdown_path = report_dir / f"{agent_name}_report.md"

    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    total = summary["total"] or 1
    hidden_compile_rate = summary["hidden_compiled"] / total
    visible_compile_rate = summary["visible_compiled"] / total
    lines = [
        f"# {agent_name} Evaluation Report",
        "",
        f"- Total tasks: {summary['total']}",
        f"- Hidden pass rate: {summary['hidden_passed']}/{summary['total']} ({summary['hidden_pass_rate']:.2%})",
        f"- Hidden compile rate: {summary['hidden_compiled']}/{summary['total']} ({hidden_compile_rate:.2%})",
        f"- Visible pass rate: {summary['visible_passed']}/{summary['total']} ({summary['visible_pass_rate']:.2%})",
        f"- Visible compile rate: {summary['visible_compiled']}/{summary['total']} ({visible_compile_rate:.2%})",
        f"- Total runtime: {summary['metrics']['runtime']['total_seconds']:.2f}s",
        f"- Average runtime: {summary['metrics']['runtime']['average_seconds']:.2f}s",
        "",
        "## Consumption Metrics",
        "",
    ]
    token_usage = summary["metrics"]["token_usage"]
    run_setup = summary.get("run_setup", {})
    if token_usage["count"]:
        lines.extend(
            [
                f"- Total tokens: {token_usage['total_tokens']}",
                f"- Average tokens per task: {token_usage['average_tokens']:.2f}",
                f"- Prompt tokens: {token_usage['prompt_tokens']}",
                f"- Completion tokens: {token_usage['completion_tokens']}",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "- Total tokens: n/a",
                "",
            ]
        )
    lines.extend(
        [
        "## Run Setup",
        "",
        f"- Identifier: {run_setup.get('identifier', agent_name)}",
        f"- Agent: {run_setup.get('agent_name', agent_name)}",
        f"- Agent version: {run_setup.get('agent_version', 'unknown')}",
        f"- Model: {run_setup.get('model_name', 'unknown')}",
        "",
        "### Initial Prompt",
        "",
        "```text",
        run_setup.get("initial_prompt", ""),
        "```",
        "",
        "## Per-Library Hidden Pass Rate",
        "",
        ]
    )
    for library, stats in summary["library_breakdown"].items():
        lines.append(f"- {library}: {stats['passed']}/{stats['total']} ({stats['pass_rate']:.2%})")
    lines.append("")
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return summary_path, markdown_path


def write_comparison_report(report_dir: Path, agent_summaries: dict[str, dict]) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    comparison_path = report_dir / "comparison.md"
    lines = [
        "# Agent Comparison",
        "",
        "| Agent | Hidden Pass | Visible Pass | Hidden Compile | Visible Compile | Avg Runtime (s) | Total Tokens |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for agent_name, summary in sorted(agent_summaries.items()):
        total = summary["total"] or 1
        token_total = summary["metrics"]["token_usage"]["total_tokens"]
        token_cell = str(token_total) if summary["metrics"]["token_usage"]["count"] else "n/a"
        lines.append(
            "| "
            + " | ".join(
                [
                    agent_name,
                    f"{summary['hidden_passed']}/{summary['total']} ({summary['hidden_pass_rate']:.2%})",
                    f"{summary['visible_passed']}/{summary['total']} ({summary['visible_pass_rate']:.2%})",
                    f"{summary['hidden_compiled']}/{summary['total']} ({summary['hidden_compiled'] / total:.2%})",
                    f"{summary['visible_compiled']}/{summary['total']} ({summary['visible_compiled'] / total:.2%})",
                    f"{summary['metrics']['runtime']['average_seconds']:.2f}",
                    token_cell,
                ]
            )
            + " |"
        )
    lines.append("")
    comparison_path.write_text("\n".join(lines), encoding="utf-8")
    return comparison_path


def is_full_benchmark_run(run_dir: Path, dataset_path: Path) -> bool:
    config_path = run_dir / "config.json"
    manifest_path = run_dir / "manifest.json"
    if not config_path.is_file() or not manifest_path.is_file():
        return False
    config = json.loads(config_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    example_ids = config.get("example_ids") or []
    limit = config.get("limit")
    tasks = manifest.get("tasks") or []
    return not example_ids and limit is None and len(tasks) == _dataset_size(dataset_path)


def archive_run_artifacts(benchmark_root: Path, run_dir: Path) -> Path:
    artifacts_root = benchmark_root / "reports" / "artifacts"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    archived_run_dir = artifacts_root / run_dir.name
    if run_dir.resolve() == archived_run_dir.resolve():
        return archived_run_dir
    if archived_run_dir.exists():
        shutil.rmtree(archived_run_dir)
    shutil.move(str(run_dir), str(archived_run_dir))
    return archived_run_dir


def update_project_history(
    project_report_dir: Path,
    run_dir: Path,
    agent_summaries: dict[str, dict],
) -> tuple[Path, Path]:
    project_report_dir.mkdir(parents=True, exist_ok=True)
    history_path = project_report_dir / "benchmark_history.jsonl"
    comparison_path = project_report_dir / "benchmark_history.md"

    existing_records: list[dict] = []
    if history_path.is_file():
        with history_path.open("r", encoding="utf-8") as handle:
            existing_records = [json.loads(line) for line in handle if line.strip()]
    for record in existing_records:
        if "identifier" not in record:
            agent = record.get("agent", "unknown")
            model_name = record.get("model_name") or "unknown"
            record["identifier"] = f"{agent}:{model_name}"
        if "agent_version" not in record:
            record["agent_version"] = record.get("agent", "unknown")
        if "initial_prompt" not in record:
            record["initial_prompt"] = ""
        if "model_name" not in record:
            record["model_name"] = "unknown"

    retained_records = existing_records[:]

    updated_at = datetime.now(timezone.utc).isoformat()
    for agent_name, summary in sorted(agent_summaries.items()):
        run_setup = summary.get("run_setup", {})
        identifier = run_setup.get("identifier", agent_name)
        retained_records = [
            record
            for record in retained_records
            if not (record.get("run_id") == run_dir.name and record.get("identifier") == identifier)
        ]
        retained_records.append(
            {
                "run_id": run_dir.name,
                "identifier": identifier,
                "agent": agent_name,
                "agent_version": run_setup.get("agent_version", agent_name),
                "model_name": run_setup.get("model_name", "unknown"),
                "initial_prompt": run_setup.get("initial_prompt", ""),
                "updated_at": updated_at,
                "run_dir": str(run_dir.relative_to(project_report_dir.parent)),
                "run_report": str((run_dir / "reports" / f"{agent_name}_report.md").relative_to(project_report_dir.parent)),
                "run_summary": str((run_dir / "reports" / f"{agent_name}_summary.json").relative_to(project_report_dir.parent)),
                "total": summary["total"],
                "hidden_passed": summary["hidden_passed"],
                "hidden_pass_rate": summary["hidden_pass_rate"],
                "hidden_compiled": summary["hidden_compiled"],
                "visible_passed": summary["visible_passed"],
                "visible_pass_rate": summary["visible_pass_rate"],
                "visible_compiled": summary["visible_compiled"],
                "avg_runtime_seconds": summary["metrics"]["runtime"]["average_seconds"],
                "total_runtime_seconds": summary["metrics"]["runtime"]["total_seconds"],
                "total_tokens": summary["metrics"]["token_usage"]["total_tokens"],
                "avg_tokens": summary["metrics"]["token_usage"]["average_tokens"],
                "token_records": summary["metrics"]["token_usage"]["count"],
            }
        )

    resolved_run_agents = {
        (record.get("run_id"), record.get("agent"))
        for record in retained_records
        if record.get("model_name") and record.get("model_name") != "unknown"
    }
    retained_records = [
        record
        for record in retained_records
        if not (
            record.get("model_name") == "unknown"
            and (record.get("run_id"), record.get("agent")) in resolved_run_agents
        )
    ]

    retained_records.sort(key=lambda record: (record["identifier"], record["run_id"]))
    history_path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in retained_records), encoding="utf-8")

    latest_by_identifier: dict[str, dict] = {}
    for record in retained_records:
        latest_by_identifier[record["identifier"]] = record

    lines = [
        "# Full Benchmark History",
        "",
        "## Latest Per Agent Model",
        "",
        "| Identifier | Run ID | Hidden Pass | Visible Pass | Avg Runtime (s) | Total Tokens | Run Report |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for identifier, record in sorted(latest_by_identifier.items()):
        token_cell = str(record["total_tokens"]) if record["token_records"] else "n/a"
        lines.append(
            "| "
            + " | ".join(
                [
                    identifier,
                    record["run_id"],
                    f"{record['hidden_passed']}/{record['total']} ({record['hidden_pass_rate']:.2%})",
                    f"{record['visible_passed']}/{record['total']} ({record['visible_pass_rate']:.2%})",
                    f"{record['avg_runtime_seconds']:.2f}",
                    token_cell,
                    f"[report]({_path_relative_to_reports(record['run_report'])})",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Run Setup",
            "",
        ]
    )
    for identifier, record in sorted(latest_by_identifier.items()):
        lines.extend(
            [
                f"### {identifier}",
                "",
                f"- Agent: {record['agent']}",
                f"- Agent version: {record['agent_version']}",
                f"- Model: {record['model_name']}",
                f"- Run ID: {record['run_id']}",
                "",
                "```text",
                record["initial_prompt"],
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "",
            "## Run History",
            "",
            "| Identifier | Run ID | Hidden Pass | Visible Pass | Avg Runtime (s) | Total Tokens | Updated At |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for record in sorted(retained_records, key=lambda item: (item["run_id"], item["identifier"]), reverse=True):
        token_cell = str(record["total_tokens"]) if record["token_records"] else "n/a"
        lines.append(
            "| "
            + " | ".join(
                [
                    record["identifier"],
                    record["run_id"],
                    f"{record['hidden_passed']}/{record['total']} ({record['hidden_pass_rate']:.2%})",
                    f"{record['visible_passed']}/{record['total']} ({record['visible_pass_rate']:.2%})",
                    f"{record['avg_runtime_seconds']:.2f}",
                    token_cell,
                    record["updated_at"],
                ]
            )
            + " |"
        )
    lines.append("")
    comparison_path.write_text("\n".join(lines), encoding="utf-8")
    return history_path, comparison_path
