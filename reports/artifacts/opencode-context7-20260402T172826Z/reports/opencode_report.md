# opencode Evaluation Report

- Total tasks: 38
- Hidden pass rate: 25/38 (65.79%)
- Hidden compile rate: 38/38 (100.00%)
- Visible pass rate: 25/38 (65.79%)
- Visible compile rate: 38/38 (100.00%)
- Total runtime: 3110.78s
- Average runtime: 81.86s

## Consumption Metrics

- Total tokens: 397281
- Average tokens per task: 10454.76
- Prompt tokens: 392890
- Completion tokens: 4391

## Run Setup

- Identifier: opencode:opencode/minimax-m2.5-free
- Agent: opencode
- Agent version: 1.1
- Model: opencode/minimax-m2.5-free
- Provider: n/a

### Initial Prompt

```text
Read and edit `{sample_path}` to complete the script by following the instructions written in the comments at the top of the sample file.
Before you generate or edit code, identify the library and version requested in the sample header comments. If documentation is needed, first use Context7 to look up the relevant API for that exact dependency version and use the retrieved docs or snippets to guide the implementation.
You should only modify that sample file, without update other files in existing workspace or install any new tools. Always check LSP diagnostic result after editing file.
```

## Per-Library Hidden Pass Rate

- django: 6/10 (60.00%)
- flask: 14/22 (63.64%)
- matplotlib: 5/6 (83.33%)
