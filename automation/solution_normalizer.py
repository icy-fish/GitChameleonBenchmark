from __future__ import annotations

import re


def extract_code(raw_text: str) -> str:
    python_match = re.search(r"```python\s*(.*?)```", raw_text, re.DOTALL | re.IGNORECASE)
    if python_match:
        return python_match.group(1).strip() + "\n"
    generic_match = re.search(r"```\s*(.*?)```", raw_text, re.DOTALL)
    if generic_match:
        return generic_match.group(1).strip() + "\n"
    return raw_text.strip() + "\n"

