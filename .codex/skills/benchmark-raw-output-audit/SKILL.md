---
name: benchmark-raw-output-audit
description: Audit a GitChameleon benchmark run from raw_outputs.jsonl, reconstruct per-task agent behavior, answer whether the agent iterated with tools or environment feedback, whether it actually passed LSP before finishing, and whether Context7 MCP usage is verifiable. Use when the user asks for a run behavior report or postmortem from raw benchmark traces.
---

# Benchmark Raw Output Audit

Use this skill when a user wants a behavior audit for a benchmark run, especially an OpenCode or Codex run archived under `runs/` or `reports/artifacts/`.

## Goal

Produce a per-task report grounded in the raw trace, not in high-level summaries. Answer these questions:

1. Did the agent try to use tools or environment feedback to improve the result?
2. If the prompt required LSP verification, did the agent actually take diagnostics seriously and finish after a clean LSP check?
3. If the prompt mentioned Context7, is there concrete evidence of Context7 MCP use before or after editing?

## Workflow

1. Inspect the run directory first.
   Expected files:
   - `config.json`
   - `manifest.json`
   - `outputs/<agent>/raw_outputs.jsonl`
   - `outputs/<agent>/solutions_eval_results.csv`
   - `task_bundles/<id>/task_bundle.json`

2. Read the agent contract.
   For OpenCode, inspect:
   - `agents/opencode/AGENTS.md`
   - `agents/opencode/agent.json`
   - `agents/opencode/prompt.txt`

3. Parse `raw_outputs.jsonl`.
   Treat each line as one task record. The important fields are:
   - `example_id`
   - `command`
   - `combined_output`
   - `solution_text`
   - `exit_code`
   - `timed_out`
   - `metrics`

4. Reconstruct behavior from JSON event lines in `combined_output`.
   Common event `type` values:
   - `tool_use`
   - `reasoning`
   - `step_start`
   - `step_finish`
   - `text`

5. Use the bundled script for the default report.
   Command:

   ```bash
   python3 .codex/skills/benchmark-raw-output-audit/scripts/audit_run.py \
     --run-dir <run_dir> \
     --compare-run <similar_non_context7_run_dir>
   ```

6. If the user asks whether Context7 was really used, prefer supplying `--compare-run` with a similar non-Context7 run. If the same generic doc tools appear in both runs, do not call that verified Context7 usage.

## Heuristics

Use these defaults unless the user asks for different criteria.

### Q1: Tool or env feedback used to improve result

Mark `Yes` when there is evidence of iteration beyond a one-shot read/edit flow:
   - more than one `edit`
   - `bash`, `glob`, `codesearch`, `webfetch`, `websearch`, or `write` after the initial edit path
   - reasoning that explicitly reacts to diagnostics or tool output

Mark `No` when the task is effectively `read -> edit -> finish` or timed out before meaningful action.

### Q2: LSP taken seriously and passed before finish

Mark `Yes` only when the trace shows a real LSP-style check, typically `pyright`, `mypy`, `ruff`, or an equivalent language-server command, and the final visible result is clean on errors.

Do not count `py_compile` or plain syntax checks as LSP compliance.

Mark `No` when:
   - there is no real LSP command
   - edit-tool diagnostics appear and the agent stops without a clean recheck
   - the agent rationalizes away diagnostics without passing a clean check

### Q3: Context7 MCP usage

Be strict. Do not infer Context7 usage from generic documentation lookups alone.

Mark `Yes` only when the trace contains concrete evidence that is attributable to Context7 MCP itself.

Mark `No verified use` when:
   - the run injected Context7 in the command or prompt, but the trace only shows generic tools such as `webfetch`, `codesearch`, or `websearch`
   - a control run without Context7 shows the same generic lookup pattern

Mark `Not needed / no evidence` when the task never needed docs and there is no lookup activity.

## Output

The report should include:
   - a short raw-output structure summary
   - run-level totals for Q1, Q2, and Q3
   - a per-task table with task id, eval result, Q1, Q2, Q3, and notes
   - a list of tasks whose behavior was not as expected, grouped by question

Keep conclusions narrow. If the trace cannot prove Context7 MCP use, say that explicitly.
