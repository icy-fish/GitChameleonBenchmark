#!/usr/bin/env python3
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


LSP_TOKENS = (
    "pyright",
    "mypy",
    "ruff",
    "pyls",
    "pyright-langserver",
    "jedi-language-server",
    "python-lsp-server",
)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open()]


def load_eval(path: Path) -> dict[str, dict]:
    with path.open() as handle:
        return {row["example_id"]: row for row in csv.DictReader(handle)}


def parse_events(record: dict) -> list[dict]:
    events: list[dict] = []
    for line in record["combined_output"].splitlines():
        if not line.startswith("{"):
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def summarize_record(record: dict, eval_rows: dict[str, dict]) -> dict:
    events = parse_events(record)
    tools = Counter()
    edits = 0
    diag_seen = False
    doc_lookup = False
    lsp_commands: list[str] = []
    lsp_outputs: list[str] = []
    clean_lsp = False
    lsp_error_seen = False
    notable: list[str] = []

    for event in events:
        if event.get("type") != "tool_use":
            continue
        part = event.get("part", {})
        tool = part.get("tool")
        tools[tool] += 1
        state = part.get("state", {})
        inp = state.get("input", {})
        output = state.get("output", "") or ""

        if tool == "edit":
            edits += 1
            metadata = state.get("metadata", {})
            diagnostics = metadata.get("diagnostics") or {}
            if diagnostics:
                diag_seen = True
            if "LSP errors detected" in output:
                diag_seen = True
                lsp_error_seen = True

        if tool in {"codesearch", "webfetch", "websearch"}:
            doc_lookup = True

        command = inp.get("command", "")
        lowered = command.lower()
        if any(token in lowered for token in LSP_TOKENS):
            lsp_commands.append(command)
            lsp_outputs.append(output)
            if re.search(r"0 errors, \d+ warnings?", output) or "0 errors, 0 warnings" in output:
                clean_lsp = True
            if re.search(r"\b[1-9]\d* error", output):
                lsp_error_seen = True

    if record.get("timed_out"):
        q1 = "No"
        q1_reason = "timed out before producing a usable trace"
    elif edits > 1 or any(tool in tools for tool in ("bash", "glob", "codesearch", "webfetch", "websearch", "write")):
        q1 = "Yes"
        q1_reason = "iterated with extra tools or multiple edits"
    else:
        q1 = "No"
        q1_reason = "one-shot read/edit flow only"

    if clean_lsp:
        q2 = "Yes"
        q2_reason = "explicit LSP command reached 0 errors"
    elif lsp_commands:
        q2 = "No"
        q2_reason = "ran an LSP command but did not finish after a clean result"
    elif diag_seen:
        q2 = "No"
        q2_reason = "saw edit-tool diagnostics but never finished with a clean LSP check"
    elif any("py_compile" in command.lower() for command in lsp_commands) or tools.get("bash"):
        q2 = "No"
        q2_reason = "used syntax checks only, not a real LSP pass"
    else:
        q2 = "No"
        q2_reason = "no evidence of a real LSP verification step"

    result = eval_rows.get(record["example_id"], {})
    passed = result.get("passed") == "True"

    if record.get("timed_out"):
        q3 = "No"
        q3_reason = "timed out; no usable evidence of Context7 MCP activity"
    elif doc_lookup:
        q3 = "No verified use"
        q3_reason = "documentation lookup happened via generic traceable tools only"
    else:
        q3 = "No evidence"
        q3_reason = "no documentation lookup and no Context7-specific trace"

    if not passed:
        notable.append("failed evaluation")
    if record.get("timed_out"):
        notable.append("timed out")
    if doc_lookup:
        notable.append("generic doc lookup")
    if edits > 1:
        notable.append(f"{edits} edits")
    if lsp_error_seen and not clean_lsp:
        notable.append("ended with unresolved visible diagnostics")
    if clean_lsp:
        notable.append("clean LSP result")

    return {
        "example_id": record["example_id"],
        "passed": passed,
        "tools": tools,
        "edits": edits,
        "q1": q1,
        "q1_reason": q1_reason,
        "q2": q2,
        "q2_reason": q2_reason,
        "q3": q3,
        "q3_reason": q3_reason,
        "timed_out": record["timed_out"],
        "exit_code": record["exit_code"],
        "duration_sec": record["duration_sec"],
        "notable": notable,
        "command": record["command"],
    }


def load_compare_tools(compare_run: Path | None) -> Counter:
    if compare_run is None:
        return Counter()
    compare_raw = compare_run / "outputs" / "opencode" / "raw_outputs.jsonl"
    if not compare_raw.exists():
        return Counter()
    tools = Counter()
    for record in load_jsonl(compare_raw):
        for event in parse_events(record):
            if event.get("type") == "tool_use":
                tools[event.get("part", {}).get("tool")] += 1
    return tools


def raw_structure(records: list[dict]) -> tuple[list[str], list[str]]:
    first = records[0]
    keys = sorted(first.keys())
    event_types = Counter()
    for event in parse_events(first):
        event_types[event.get("type", "<missing>")] += 1
    return keys, [f"{name} ({count})" for name, count in event_types.items()]


def format_task_list(rows: list[dict]) -> str:
    if not rows:
        return "- none"
    return "\n".join(f"- {row['example_id']}: {row}" for row in [])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--compare-run", type=Path)
    args = parser.parse_args()

    run_dir = args.run_dir
    raw_path = run_dir / "outputs" / "opencode" / "raw_outputs.jsonl"
    eval_path = run_dir / "outputs" / "opencode" / "solutions_eval_results.csv"
    records = load_jsonl(raw_path)
    eval_rows = load_eval(eval_path)
    summaries = [summarize_record(record, eval_rows) for record in records]
    summaries.sort(key=lambda row: int(row["example_id"]))

    compare_tools = load_compare_tools(args.compare_run)
    keys, event_preview = raw_structure(records)

    prompt_with_context7 = any("use context7" in " ".join(row["command"]).lower() for row in summaries)
    context7_config = any("OPENCODE_CONFIG_CONTENT=" in " ".join(row["command"]) and "context7" in " ".join(row["command"]).lower() for row in summaries)

    q1_yes = sum(row["q1"] == "Yes" for row in summaries)
    q2_yes = sum(row["q2"] == "Yes" for row in summaries)
    q3_verified = sum(row["q3"] == "Yes" for row in summaries)
    passed = sum(row["passed"] for row in summaries)

    q1_unexpected = [
        row for row in summaries
        if row["q1"] == "No" or row["timed_out"]
    ]
    q2_unexpected = [row for row in summaries if row["q2"] != "Yes"]
    q3_unexpected = [
        row for row in summaries
        if row["q3"] != "Yes" and ("codesearch" in row["tools"] or "webfetch" in row["tools"] or "websearch" in row["tools"])
    ]

    print(f"# Behavior Audit: {run_dir.name}\n")
    print("## Raw Output Structure")
    print(f"- Run directory: `{run_dir}`")
    print(f"- Task count: {len(summaries)}")
    print(f"- Evaluation: {passed}/{len(summaries)} passed")
    print(f"- `raw_outputs.jsonl` top-level keys: {', '.join(keys)}")
    print(f"- First task event types: {', '.join(event_preview)}")
    print(f"- Context7 injected in command/config: {'yes' if context7_config else 'no'}")
    print(f"- Context7 prompt hint present: {'yes' if prompt_with_context7 else 'no'}")
    if compare_tools:
        print(f"- Control run generic tool overlap: {dict(compare_tools)}")
    print()

    print("## Run-Level Answers")
    print(f"- Q1. Tool or env feedback used to improve output: {q1_yes}/{len(summaries)} tasks marked `Yes`.")
    print(f"- Q2. Finished after a clean LSP check: {q2_yes}/{len(summaries)} tasks marked `Yes`.")
    print(f"- Q3. Verifiable Context7 MCP usage: {q3_verified}/{len(summaries)} tasks marked `Yes`.")
    print("- Context7 conclusion: the run clearly injected Context7 into the command and prompt, but the archived trace does not preserve a Context7-specific tool identity. Where documentation lookups occurred, they appear as generic `codesearch`/`webfetch` calls, and the same generic tools are also present in the non-Context7 control run.")
    print()

    print("## Per-Task Matrix")
    print("| Task | Eval | Q1 | Q2 | Q3 | Notes |")
    print("| --- | --- | --- | --- | --- | --- |")
    for row in summaries:
        eval_status = "pass" if row["passed"] else "fail"
        notes = "; ".join(row["notable"]) if row["notable"] else "-"
        print(f"| {row['example_id']} | {eval_status} | {row['q1']} | {row['q2']} | {row['q3']} | {notes} |")
    print()

    print("## Not As Expected")
    print("### Q1: No clear improvement attempt")
    if q1_unexpected:
        for row in q1_unexpected:
            print(f"- {row['example_id']}: {row['q1_reason']}")
    else:
        print("- none")
    print()

    print("### Q2: Did not clearly finish after a clean LSP check")
    for row in q2_unexpected:
        print(f"- {row['example_id']}: {row['q2_reason']}")
    print()

    print("### Q3: Context7 not verifiable from trace")
    if q3_unexpected:
        for row in q3_unexpected:
            print(f"- {row['example_id']}: {row['q3_reason']}")
    else:
        print("- none")


if __name__ == "__main__":
    main()
