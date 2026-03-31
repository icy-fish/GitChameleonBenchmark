from __future__ import annotations

import subprocess
from pathlib import Path


def evaluate_solutions(
    benchmark_root: Path,
    solution_file: Path,
    workers: int,
    docker_image: str | None = None,
    docker_tag: str | None = None,
) -> Path:
    command = [
        "python3",
        "-m",
        "gitchameleon.eval_wrapper",
        "--solution-path",
        str(solution_file.resolve()),
        "--workers",
        str(workers),
    ]
    if docker_image:
        command.extend(["--docker-image", docker_image])
    if docker_tag:
        command.extend(["--docker-tag", docker_tag])

    subprocess.run(command, cwd=benchmark_root, check=True)
    return solution_file.with_name(f"{solution_file.stem}_eval_results.csv")
