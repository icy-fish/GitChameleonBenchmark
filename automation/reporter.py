from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from automation.backends.opencode import OpencodeBackend


def _load_dataset_index(dataset_path: Path) -> dict[str, dict]:
    with dataset_path.open("r", encoding="utf-8") as handle:
        return {str(row["example_id"]): row for row in (json.loads(line) for line in handle if line.strip())}


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
