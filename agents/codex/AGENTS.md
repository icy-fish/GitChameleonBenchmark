# Codex Agent Notes

This folder provides the Codex contract consumed by the benchmark harness:

- `agent.json` defines the Codex CLI command, environment, model default, and result-file behavior
- `prompt.txt` defines the prompt template rendered per task

## Runtime Contract

For each task, the harness prepares a task workspace and runs Codex with that workspace as its root.

The task workspace contains:

- `sample_{i}.py`, generated from the dataset row
- the mounted task venv at `.dataset_venvs/gcham_venv_*`

Codex is expected to:

1. Read `sample_{i}.py`
2. Use the task venv when package-aware inspection is needed
3. Edit `sample_{i}.py` in place with the completed final answer
4. Keep task execution traces in stdout/stderr so the harness can store them in `agent_log.txt`

The harness reads the final answer from the edited `sample_{i}.py`.

## Default Codex Config

`agent.json` currently sets these defaults:

- model: `gpt-5-codex`
- result file: `sample_{example_id}.py`
- output mode: `codex exec --json`
- execution mode: full-auto, non-interactive
- auth source: the worker reuses the operator's local Codex home, including `auth.json`
- provider: `openai` by default; the harness can override this to `openrouter`

## Provider Overrides

Codex benchmark runs can target either:

- `openai`: default Codex provider behavior
- `openrouter`: injected at runtime with `codex exec -c ...` provider config overrides

OpenRouter runs require `OPENROUTER_API_KEY` in the benchmark worker environment. The harness also mirrors that value into `OPENAI_API_KEY` when needed so Codex versions that still consult the OpenAI env key can run against OpenRouter.

## Canonical Commands

Prepare tasks:

```bash
python3 -m automation.cli prepare --run-id codex-smoke --agents codex --example-ids 99
```

Run Codex with folder-defined defaults:

```bash
python3 -m automation.cli run-agent --run-id codex-smoke --agent codex
```

Run Codex through OpenRouter:

```bash
python3 -m automation.cli run-agent --run-id codex-smoke --agent codex --provider openrouter --model openai/gpt-5.4
```

Evaluate results:

```bash
python3 -m automation.cli evaluate --run-id codex-smoke --agent codex
```
