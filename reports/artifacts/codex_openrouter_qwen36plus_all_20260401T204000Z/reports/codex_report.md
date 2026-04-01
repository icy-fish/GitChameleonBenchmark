# codex Evaluation Report

- Total tasks: 38
- Hidden pass rate: 21/38 (55.26%)
- Hidden compile rate: 38/38 (100.00%)
- Visible pass rate: 19/38 (50.00%)
- Visible compile rate: 30/38 (78.95%)
- Total runtime: 3082.02s
- Average runtime: 81.11s

## Consumption Metrics

- Total tokens: 2656326
- Average tokens per task: 69903.32
- Prompt tokens: 2598814
- Completion tokens: 57512

## Run Setup

- Identifier: codex:qwen/qwen3.6-plus-preview:free
- Agent: codex
- Agent version: codex
- Model: qwen/qwen3.6-plus-preview:free
- Provider: openrouter

### Initial Prompt

```text
Read and edit `{sample_path}` to complete the script by following the instructions written in the comments at the top of the sample file. Only modify that sample file.
```

## Per-Library Hidden Pass Rate

- django: 5/10 (50.00%)
- flask: 12/22 (54.55%)
- matplotlib: 4/6 (66.67%)
