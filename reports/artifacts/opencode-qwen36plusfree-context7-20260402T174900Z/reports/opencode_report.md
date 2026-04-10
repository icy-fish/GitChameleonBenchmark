# opencode Evaluation Report

- Total tasks: 38
- Hidden pass rate: 20/38 (52.63%)
- Hidden compile rate: 38/38 (100.00%)
- Visible pass rate: 21/38 (55.26%)
- Visible compile rate: 29/38 (76.32%)
- Total runtime: 18794.31s
- Average runtime: 494.59s

## Consumption Metrics

- Total tokens: 563924
- Average tokens per task: 18797.47
- Prompt tokens: 539856
- Completion tokens: 24068

## Run Setup

- Identifier: opencode:opencode/qwen3.6-plus-free
- Agent: opencode
- Agent version: 1.1
- Model: opencode/qwen3.6-plus-free
- Provider: n/a

### Initial Prompt

```text
Read and edit `{sample_path}` to complete the script by following the instructions written in the comments at the top of the sample file.
Before you generate or edit code, identify the library and version requested in the sample header comments. If documentation is needed, first use Context7 to look up the relevant API for that exact dependency version and use the retrieved docs or snippets to guide the implementation.
You should only modify that sample file, without update other files in existing workspace or install any new tools. Always check LSP diagnostic result after editing file.
```

## Per-Library Hidden Pass Rate

- django: 5/10 (50.00%)
- flask: 14/22 (63.64%)
- matplotlib: 1/6 (16.67%)
