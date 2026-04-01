# opencode Evaluation Report

- Total tasks: 38
- Hidden pass rate: 22/38 (57.89%)
- Hidden compile rate: 38/38 (100.00%)
- Visible pass rate: 21/38 (55.26%)
- Visible compile rate: 38/38 (100.00%)
- Total runtime: 1539.50s
- Average runtime: 40.51s

## Consumption Metrics

- Total tokens: 45759
- Average tokens per task: 1204.18
- Prompt tokens: 38853
- Completion tokens: 6906

## Run Setup

- Identifier: opencode:openrouter/openai/gpt-5.4
- Agent: opencode
- Agent version: 1.1
- Model: openrouter/openai/gpt-5.4
- Provider: openrouter

### Initial Prompt

```text
Read and edit `{sample_path}` to complete the script by following the instructions written in the comments at the top of the sample file.
You should only modify that sample file. Always verify the edited sample file with LSP. Do not execute the Python file in this workspace.
```

## Per-Library Hidden Pass Rate

- django: 4/10 (40.00%)
- flask: 14/22 (63.64%)
- matplotlib: 4/6 (66.67%)
