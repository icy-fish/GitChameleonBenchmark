from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gitchameleon.utils import generate_venv_cache_key


@dataclass(frozen=True)
class TaskBundle:
    example_id: str
    python_version: str
    library: str
    version: str
    additional_dependencies: str
    problem: str
    starting_code: str
    visible_test: str | None = None

    @classmethod
    def from_dataset_row(cls, row: dict[str, Any], include_visible_test: bool) -> "TaskBundle":
        return cls(
            example_id=str(row["example_id"]),
            python_version=row["python_version"],
            library=row["library"],
            version=row["version"],
            additional_dependencies=(row.get("additional_dependencies") or "").strip(),
            problem=row["problem"],
            starting_code=row["starting_code"],
            visible_test=row.get("test") if include_visible_test else None,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskBundle":
        return cls(
            example_id=str(data["example_id"]),
            python_version=data["python_version"],
            library=data["library"],
            version=data["version"],
            additional_dependencies=(data.get("additional_dependencies") or "").strip(),
            problem=data["problem"],
            starting_code=data["starting_code"],
            visible_test=data.get("visible_test"),
        )

    def to_dict(self) -> dict[str, Any]:
        data = {
            "example_id": self.example_id,
            "python_version": self.python_version,
            "library": self.library,
            "version": self.version,
            "additional_dependencies": self.additional_dependencies,
            "problem": self.problem,
            "starting_code": self.starting_code,
        }
        if self.visible_test is not None:
            data["visible_test"] = self.visible_test
        return data

    def requirement_lines(self) -> list[str]:
        requirements = [f"{self.library}=={self.version}"]
        if self.additional_dependencies:
            requirements.extend(dep for dep in self.additional_dependencies.split() if dep and dep != "-")
        deduped: list[str] = []
        seen: set[str] = set()
        for requirement in requirements:
            if requirement not in seen:
                seen.add(requirement)
                deduped.append(requirement)
        return deduped

    def venv_name(self) -> str:
        env_key = generate_venv_cache_key(
            self.python_version,
            self.library,
            self.version,
            self.additional_dependencies or "",
        )
        return f"gcham_venv_{env_key}"

    def sample_filename(self) -> str:
        return f"sample_{self.example_id}.py"

    def result_filename(self) -> str:
        return f"result_{self.example_id}.py"

    def render_sample(self) -> str:
        problem = self.problem.replace("\n", ";").strip()
        return (
            "# Complete using the following libraries and / or extra dependencies and their versions:\n"
            f"# problem statement: {problem}\n"
            f"# library: {self.library}\n"
            f"# version: {self.version}\n"
            f"# extra_dependencies: {self.additional_dependencies}\n\n"
            f"{self.starting_code.rstrip()}\n"
        )
