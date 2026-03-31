# OpenCode Agent Notes

This folder provides the OpenCode contract consumed by the benchmark harness:

- `Dockerfile` builds the runner image
- `agent.json` defines the image, command, environment, workspace path, and result-file behavior
- `prompt.txt` defines the prompt template rendered per task

## Runtime Contract

For each task, the harness prepares a host workspace and then runs OpenCode inside a temporary runtime copy mounted at `/app`.

The runtime workspace contains:

- `sample_{i}.py`, generated from the dataset row
- task metadata files such as `prompt.md` and `task_bundle.json`
- the task venv mounted at `/app/.dataset_venvs/gcham_venv_*`

OpenCode is expected to:

1. Read `sample_{i}.py`
2. Use the mounted task venv when it needs package-aware inspection
3. Write the completed answer back into `sample_{i}.py`
4. Keep the task-local trace in console output, which the harness stores in `agent_log.txt`

The harness reads the final answer from the edited runtime copy of `sample_{i}.py`. The prepared host-side `sample_{i}.py` is only an input artifact and must remain unchanged.

The harness also captures per-task runtime metadata in `raw_outputs.jsonl`, including:

- `started_at` and `completed_at` in UTC
- `duration_sec` for wall-clock execution time
- `metrics.token_usage` when OpenCode emits usage data

## Sample File Format

`sample_{i}.py` is generated with this structure:

```text
# Complete using the following libraries and / or extra dependencies and their versions:
# problem statement: ...
# library: ...
# version: ...
# extra_dependencies: ...

{starting_code}
```

The problem statement is flattened onto one line by replacing `\n` with `;`.

## Default OpenCode Config

`agent.json` currently sets these defaults:

- image: `gitchameleon-opencode:1.1`
- model: `opencode/minimax-m2.5-free`
- workspace: `/app`
- network: `bridge`
- writable OpenCode state under `/tmp/opencode-home`
- result file: `sample_{example_id}.py`
- output format: JSON events via `opencode run --format json`

The default command passes the rendered prompt to OpenCode. That prompt is built from `prompt.txt` with task-specific placeholders such as `{sample_path}`, `{result_path}`, and `{task_venv}`.

## Logs And Verification

For each task, the harness writes:

- `agent_log.txt`: exact launch command plus merged stdout/stderr
- `agent_stdout.txt`: merged process output for compatibility
- `agent_stderr.txt`: currently empty for merged-stream runs
- `raw_outputs.jsonl`: per-task execution records, including duration and parsed token usage when available

The canonical smoke-test flow is:

```bash
python3 -m automation.cli prepare --run-id opencode-smoke --agents opencode --example-ids 99
python3 -m automation.cli run-agent --run-id opencode-smoke --agent opencode
python3 -m automation.cli evaluate --run-id opencode-smoke --agent opencode
```
