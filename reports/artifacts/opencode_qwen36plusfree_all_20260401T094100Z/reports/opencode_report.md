# opencode Evaluation Report

- Total tasks: 38
- Hidden pass rate: 24/38 (63.16%)
- Hidden compile rate: 38/38 (100.00%)
- Visible pass rate: 21/38 (55.26%)
- Visible compile rate: 38/38 (100.00%)
- Total runtime: 3613.03s
- Average runtime: 95.08s

## Consumption Metrics

- Total tokens: 557220
- Average tokens per task: 14663.68
- Prompt tokens: 535951
- Completion tokens: 21269

## Run Setup

- Identifier: opencode:opencode/qwen3.6-plus-free
- Agent: opencode
- Agent version: 1.1
- Model: opencode/qwen3.6-plus-free

### Initial Prompt

```text
Read and edit `{sample_path}` to complete the script by following the instructions written in the comments at the top of the sample file.
You should only modify that sample file. Always verify the edited sample file with LSP. Do not execute the Python file in this workspace.
```

## Per-Library Hidden Pass Rate

- django: 4/10 (40.00%)
- flask: 17/22 (77.27%)
- matplotlib: 3/6 (50.00%)
