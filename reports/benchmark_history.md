# Full Benchmark History

## Latest Per Agent Model

| Identifier | Run ID | Hidden Pass | Visible Pass | Avg Runtime (s) | Total Tokens | Run Report |
| --- | --- | --- | --- | --- | --- | --- |
| codex:gpt-5.4 | codex_gpt54_all_20260401T151818Z | 25/38 (65.79%) | 27/38 (71.05%) | 37.85 | n/a | [report](artifacts/codex_gpt54_all_20260401T151818Z/reports/codex_report.md) |
| codex:qwen/qwen3.6-plus-preview:free | codex_openrouter_qwen36plus_all_20260401T204000Z | 21/38 (55.26%) | 19/38 (50.00%) | 81.11 | 2656326 | [report](artifacts/codex_openrouter_qwen36plus_all_20260401T204000Z/reports/codex_report.md) |
| opencode:opencode/mimo-v2-pro-free | opencode-mimov2profree-full-20260401 | 21/38 (55.26%) | 22/38 (57.89%) | 114.45 | 278426 | [report](artifacts/opencode-mimov2profree-full-20260401/reports/opencode_report.md) |
| opencode:opencode/minimax-m2.5-free | opencode_all_20260331T194900Z | 22/38 (57.89%) | 19/38 (50.00%) | 43.06 | 390286 | [report](artifacts/opencode_all_20260331T194900Z/reports/opencode_report.md) |
| opencode:opencode/minimax-m2.5-free:context7 | opencode-context7-20260402T172826Z | 25/38 (65.79%) | 25/38 (65.79%) | 81.86 | 397281 | [report](artifacts/opencode-context7-20260402T172826Z/reports/opencode_report.md) |
| opencode:opencode/qwen3.6-plus-free | opencode_qwen36plusfree_all_20260401T094100Z | 24/38 (63.16%) | 21/38 (55.26%) | 95.08 | 557220 | [report](artifacts/opencode_qwen36plusfree_all_20260401T094100Z/reports/opencode_report.md) |
| opencode:openrouter/openai/gpt-5.4 | opencode-openrouter-gpt54-full-20260401 | 22/38 (57.89%) | 21/38 (55.26%) | 40.51 | 45759 | [report](artifacts/opencode-openrouter-gpt54-full-20260401/reports/opencode_report.md) |
| opencode:openrouter/z-ai/glm-5 | opencode-openrouter-glm5-full-20260401 | 24/38 (63.16%) | 24/38 (63.16%) | 56.45 | 206726 | [report](artifacts/opencode-openrouter-glm5-full-20260401/reports/opencode_report.md) |

## Run Setup

### codex:gpt-5.4

- Agent: codex
- Agent version: codex
- Model: gpt-5.4
- Provider: n/a
- Run ID: codex_gpt54_all_20260401T151818Z

```text
Read and edit `{sample_path}` to complete the script by following the instructions written in the comments at the top of the sample file. Only modify that sample file.
```

### codex:qwen/qwen3.6-plus-preview:free

- Agent: codex
- Agent version: codex
- Model: qwen/qwen3.6-plus-preview:free
- Provider: openrouter
- Run ID: codex_openrouter_qwen36plus_all_20260401T204000Z

```text
Read and edit `{sample_path}` to complete the script by following the instructions written in the comments at the top of the sample file. Only modify that sample file.
```

### opencode:opencode/mimo-v2-pro-free

- Agent: opencode
- Agent version: 1.1
- Model: opencode/mimo-v2-pro-free
- Provider: n/a
- Run ID: opencode-mimov2profree-full-20260401

```text
Read and edit `{sample_path}` to complete the script by following the instructions written in the comments at the top of the sample file.
You should only modify that sample file. Always verify the edited sample file with LSP. Do not execute the Python file in this workspace.
```

### opencode:opencode/minimax-m2.5-free

- Agent: opencode
- Agent version: 1.1
- Model: opencode/minimax-m2.5-free
- Provider: n/a
- Run ID: opencode_all_20260331T194900Z

```text
Read and edit `{sample_path}` to complete the script by following the instructions written in the comments at the top of the sample file.
You should only modify that sample file. Always verify the edited sample file with LSP. Do not execute the Python file in this workspace.
```

### opencode:opencode/minimax-m2.5-free:context7

- Agent: opencode
- Agent version: 1.1
- Model: opencode/minimax-m2.5-free
- Provider: n/a
- Run ID: opencode-context7-20260402T172826Z
- Task setup: full dataset, 4 workers, Context7 MCP enabled

```text
Read and edit `{sample_path}` to complete the script by following the instructions written in the comments at the top of the sample file.
Before you generate or edit code, identify the library and version requested in the sample header comments. If documentation is needed, first use Context7 to look up the relevant API for that exact dependency version and use the retrieved docs or snippets to guide the implementation.
You should only modify that sample file, without update other files in existing workspace or install any new tools. Always check LSP diagnostic result after editing file.
```

### opencode:opencode/qwen3.6-plus-free

- Agent: opencode
- Agent version: 1.1
- Model: opencode/qwen3.6-plus-free
- Provider: n/a
- Run ID: opencode_qwen36plusfree_all_20260401T094100Z

```text
Read and edit `{sample_path}` to complete the script by following the instructions written in the comments at the top of the sample file.
You should only modify that sample file. Always verify the edited sample file with LSP. Do not execute the Python file in this workspace.
```

### opencode:openrouter/openai/gpt-5.4

- Agent: opencode
- Agent version: 1.1
- Model: openrouter/openai/gpt-5.4
- Provider: openrouter
- Run ID: opencode-openrouter-gpt54-full-20260401

```text
Read and edit `{sample_path}` to complete the script by following the instructions written in the comments at the top of the sample file.
You should only modify that sample file. Always verify the edited sample file with LSP. Do not execute the Python file in this workspace.
```

### opencode:openrouter/z-ai/glm-5

- Agent: opencode
- Agent version: 1.1
- Model: openrouter/z-ai/glm-5
- Provider: openrouter
- Run ID: opencode-openrouter-glm5-full-20260401

```text
Read and edit `{sample_path}` to complete the script by following the instructions written in the comments at the top of the sample file.
You should only modify that sample file. Always verify the edited sample file with LSP. Do not execute the Python file in this workspace.
```


## Run History

| Identifier | Run ID | Hidden Pass | Visible Pass | Avg Runtime (s) | Total Tokens | Updated At |
| --- | --- | --- | --- | --- | --- | --- |
| opencode:opencode/qwen3.6-plus-free | opencode_qwen36plusfree_all_20260401T094100Z | 24/38 (63.16%) | 21/38 (55.26%) | 95.08 | 557220 | 2026-04-01T09:59:24.666915+00:00 |
| opencode:opencode/minimax-m2.5-free | opencode_all_20260331T194900Z | 22/38 (57.89%) | 19/38 (50.00%) | 43.06 | 390286 | 2026-04-01T09:32:29.839741+00:00 |
| opencode:openrouter/openai/gpt-5.4 | opencode-openrouter-gpt54-full-20260401 | 22/38 (57.89%) | 21/38 (55.26%) | 40.51 | 45759 | 2026-04-01T20:27:51.106328+00:00 |
| opencode:openrouter/z-ai/glm-5 | opencode-openrouter-glm5-full-20260401 | 24/38 (63.16%) | 24/38 (63.16%) | 56.45 | 206726 | 2026-04-01T20:12:29.577351+00:00 |
| opencode:opencode/mimo-v2-pro-free | opencode-mimov2profree-full-20260401 | 21/38 (55.26%) | 22/38 (57.89%) | 114.45 | 278426 | 2026-04-01T22:05:35.735593+00:00 |
| opencode:opencode/minimax-m2.5-free:context7 | opencode-context7-20260402T172826Z | 25/38 (65.79%) | 25/38 (65.79%) | 81.86 | 397281 | 2026-04-02T17:43:29.834060+00:00 |
| codex:qwen/qwen3.6-plus-preview:free | codex_openrouter_qwen36plus_all_20260401T204000Z | 21/38 (55.26%) | 19/38 (50.00%) | 81.11 | 2656326 | 2026-04-01T19:04:40.550974+00:00 |
| codex:gpt-5.4 | codex_gpt54_all_20260401T151818Z | 25/38 (65.79%) | 27/38 (71.05%) | 37.85 | n/a | 2026-04-01T15:44:43.582094+00:00 |
