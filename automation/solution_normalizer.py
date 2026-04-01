from __future__ import annotations

import re


def extract_code(raw_text: str) -> str:
    python_match = re.search(r"```python\s*(.*?)```", raw_text, re.DOTALL | re.IGNORECASE)
    if python_match:
        return _strip_sample_header(python_match.group(1).strip()) + "\n"
    generic_match = re.search(r"```\s*(.*?)```", raw_text, re.DOTALL)
    if generic_match:
        return _strip_sample_header(generic_match.group(1).strip()) + "\n"
    return _strip_sample_header(raw_text.strip()) + "\n"


def _strip_sample_header(text: str) -> str:
    lines = text.splitlines()
    if len(lines) < 5:
        return text
    expected_prefixes = [
        "# Complete using the following libraries and / or extra dependencies and their versions:",
        "# problem statement:",
        "# library:",
        "# version:",
        "# extra_dependencies:",
    ]
    for index, prefix in enumerate(expected_prefixes):
        if not lines[index].startswith(prefix):
            return text
    start_index = len(expected_prefixes)
    while start_index < len(lines) and not lines[start_index].strip():
        start_index += 1
    return "\n".join(lines[start_index:]).strip()
