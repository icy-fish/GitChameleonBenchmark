from __future__ import annotations

import json
from pathlib import Path

from automation.models import TaskBundle


def load_dataset_rows(dataset_path: Path) -> list[dict]:
    with dataset_path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def select_dataset_rows(
    dataset_rows: list[dict],
    example_ids: list[str] | None = None,
    limit: int | None = None,
) -> list[dict]:
    selected = dataset_rows
    if example_ids:
        wanted = {str(example_id) for example_id in example_ids}
        selected = [row for row in dataset_rows if str(row["example_id"]) in wanted]
    if limit is not None:
        selected = selected[:limit]
    return selected


def build_task_bundles(
    dataset_path: Path,
    output_dir: Path,
    example_ids: list[str] | None = None,
    limit: int | None = None,
    include_visible_tests: bool = False,
) -> list[TaskBundle]:
    dataset_rows = load_dataset_rows(dataset_path)
    selected_rows = select_dataset_rows(dataset_rows, example_ids=example_ids, limit=limit)

    output_dir.mkdir(parents=True, exist_ok=True)
    bundles: list[TaskBundle] = []
    for row in selected_rows:
        bundle = TaskBundle.from_dataset_row(row, include_visible_test=include_visible_tests)
        bundle_dir = output_dir / bundle.example_id
        bundle_dir.mkdir(parents=True, exist_ok=True)
        (bundle_dir / "task_bundle.json").write_text(
            json.dumps(bundle.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (bundle_dir / "starting_code.py").write_text(bundle.starting_code, encoding="utf-8")
        (bundle_dir / "requirements.txt").write_text("\n".join(bundle.requirement_lines()) + "\n", encoding="utf-8")
        bundles.append(bundle)
    return bundles

