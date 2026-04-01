# opencode Evaluation Report

- Total tasks: 38
- Hidden pass rate: 24/38 (63.16%)
- Hidden compile rate: 38/38 (100.00%)
- Visible pass rate: 24/38 (63.16%)
- Visible compile rate: 38/38 (100.00%)
- Total runtime: 2145.24s
- Average runtime: 56.45s

## Consumption Metrics

- Total tokens: 206726
- Average tokens per task: 5440.16
- Prompt tokens: 191932
- Completion tokens: 14794

## Run Setup

- Identifier: opencode:openrouter/z-ai/glm-5
- Agent: opencode
- Agent version: 1.1
- Model: openrouter/z-ai/glm-5
- Provider: openrouter

### Initial Prompt

```text
Read and edit `{sample_path}` to complete the script by following the instructions written in the comments at the top of the sample file.
You should only modify that sample file. Always verify the edited sample file with LSP. Do not execute the Python file in this workspace.
```

## Per-Library Hidden Pass Rate

- django: 6/10 (60.00%)
- flask: 14/22 (63.64%)
- matplotlib: 4/6 (66.67%)
