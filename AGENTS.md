# Benchmark Harness Workflow

This repository treats `agents/{agent_name}` as the source of truth for running an agent in the benchmark harness.

When asked to run a benchmark for an agent:

1. Inspect `agents/{agent_name}` first.
2. Derive runtime behavior from the files in that folder instead of relying on automation defaults.
3. Only use explicit CLI overrides when the user asks for them.

## Agent Folder Contract

Treat these files as the agent contract:

- `AGENTS.md`: human-facing workflow notes and agent-specific caveats
- `agent.json`: machine-readable image, command, environment, prompt file, and output-file defaults
- `prompt.txt`: default prompt template when referenced by `agent.json`
- `Dockerfile`: image definition used by the harness when the agent image is missing

## Harness Contract

The automation harness is expected to behave as follows:

- `prepare` creates one prepared workspace per task under `/tmp/gitchameleon_agent_workspaces/{run_id}/{agent}/{example_id}`
- each prepared workspace contains `sample_{i}.py`, `prompt.md`, task metadata, and `starting_code.py`
- each task has a prebuilt venv at `.dataset_venvs/gcham_venv_*`, selected from task metadata and mounted into the container
- containerized runs execute in a temporary runtime copy of the prepared workspace, mounted inside the container at the agent-defined workspace path, typically `/app`
- edits made by the agent inside the container must be captured from that runtime copy and must not mutate the prepared host workspace
- the harness reads the final answer from the agent-defined result file when configured, otherwise it falls back to stdout
- `agent_log.txt` must contain the exact launch command first, then the merged stdout/stderr stream in execution order
- `raw_outputs.jsonl` must retain per-task run metadata including start/end timestamps, wall-clock duration, and any structured consumption metrics captured from the agent backend
- `report` output should summarize both correctness metrics and consumption metrics, including runtime and token usage when available
- full-dataset benchmark runs should also update project-level history artifacts under `reports/`, preserving a per-run record and a cross-run comparison view
- full-dataset benchmark runs that are included in project history should be moved from `runs/` into `reports/artifacts/{run_id}/`

## Sample File Workflow

The default sample file generated for each task is:

```text
# Complete using the following libraries and / or extra dependencies and their versions:
# problem statement: ...
# library: ...
# version: ...
# extra_dependencies: ...

{starting_code}
```

The problem statement is flattened by replacing newlines with `;`.

If an agent is configured to edit `sample_{i}.py` directly, the harness must:

- point the result path at that sample file
- capture the edited sample from the temporary runtime workspace
- leave the prepared host-side `sample_{i}.py` unchanged

## OpenCode Notes

For `agents/opencode`:

- the workspace path inside the container is `/app`
- the task venv is mounted at `/app/.dataset_venvs/gcham_venv_*`
- prompt text comes from `agents/opencode/prompt.txt`
- runtime defaults come from `agents/opencode/agent.json`
- OpenCode currently solves tasks by editing `sample_{i}.py` directly rather than creating `result_{i}.py`
- OpenCode runs should use JSON event output so the harness can extract token usage when the CLI emits it

## Canonical Commands

Prepare tasks:

```bash
python3 -m automation.cli prepare --run-id <run_id> --agents <agent_name> --example-ids <id>
```

Run an agent with its folder-defined defaults:

```bash
python3 -m automation.cli run-agent --run-id <run_id> --agent <agent_name>
```

Evaluate results:

```bash
python3 -m automation.cli evaluate --run-id <run_id> --agent <agent_name>
```
