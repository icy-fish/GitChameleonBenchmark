# opencode Evaluation Report

- Total tasks: 38
- Hidden pass rate: 22/38 (57.89%)
- Hidden compile rate: 38/38 (100.00%)
- Visible pass rate: 19/38 (50.00%)
- Visible compile rate: 38/38 (100.00%)
- Total runtime: 1636.15s
- Average runtime: 43.06s

## Consumption Metrics

- Total tokens: 390286
- Average tokens per task: 10270.68
- Prompt tokens: 385726
- Completion tokens: 4560

## Run Setup

- Identifier: opencode:opencode/minimax-m2.5-free
- Agent: opencode
- Agent version: 1.1
- Model: opencode/minimax-m2.5-free

### Initial Prompt

```text
Read and edit `{sample_path}` to complete the script by following the instructions written in the comments at the top of the sample file.
You should only modify that sample file. Always verify the edited sample file with LSP. Do not execute the Python file in this workspace.
```

## Per-Library Hidden Pass Rate

- django: 5/10 (50.00%)
- flask: 12/22 (54.55%)
- matplotlib: 5/6 (83.33%)
