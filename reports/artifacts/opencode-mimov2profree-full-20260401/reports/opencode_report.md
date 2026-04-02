# opencode Evaluation Report

- Total tasks: 38
- Hidden pass rate: 21/38 (55.26%)
- Hidden compile rate: 38/38 (100.00%)
- Visible pass rate: 22/38 (57.89%)
- Visible compile rate: 37/38 (97.37%)
- Total runtime: 4349.20s
- Average runtime: 114.45s

## Consumption Metrics

- Total tokens: 278426
- Average tokens per task: 7327.00
- Prompt tokens: 269413
- Completion tokens: 9013

## Run Setup

- Identifier: opencode:opencode/mimo-v2-pro-free
- Agent: opencode
- Agent version: 1.1
- Model: opencode/mimo-v2-pro-free
- Provider: n/a

### Initial Prompt

```text
Read and edit `{sample_path}` to complete the script by following the instructions written in the comments at the top of the sample file.
You should only modify that sample file. Always verify the edited sample file with LSP. Do not execute the Python file in this workspace.
```

## Per-Library Hidden Pass Rate

- django: 3/10 (30.00%)
- flask: 16/22 (72.73%)
- matplotlib: 2/6 (33.33%)
