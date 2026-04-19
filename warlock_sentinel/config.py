from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class LLMConfig:
    provider: str = "gemini"
    model: str = "gemini-2.5-pro"
    api_key_env: str = "GEMINI_API_KEY"
    temperature: float = 0.2


@dataclass(slots=True)
class CoverageConfig:
    target: int = 85
    include: list[str] = field(default_factory=lambda: ["lib/**", "src/**"])
    exclude: list[str] = field(
        default_factory=lambda: ["**/*.g.dart", "**/*.gen.ts", "**/node_modules/**"]
    )


@dataclass(slots=True)
class GenerationConfig:
    max_files_per_run: int = 20
    max_iterations: int = 6
    write_mode: str = "overwrite"
    test_style: str = "pragmatic"
    flutter: dict[str, Any] = field(default_factory=dict)
    react: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OutputConfig:
    dashboard_path: str = ".warlock/dashboard.html"
    report_json_path: str = ".warlock/report.json"


@dataclass(slots=True)
class SentinelConfig:
    project_name: str
    framework: str = "auto"
    llm: LLMConfig = field(default_factory=LLMConfig)
    coverage: CoverageConfig = field(default_factory=CoverageConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def defaults(cls, project_name: str) -> "SentinelConfig":
        return cls(project_name=project_name)

    @classmethod
    def load(cls, path: Path) -> "SentinelConfig | None":
        if not path.exists():
            return None

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ConfigValidationError("Configuration file must contain a YAML mapping at root level")

        config = cls(
            project_name=str(data.get("project_name", path.parent.name)),
            framework=str(data.get("framework", "auto")),
            llm=LLMConfig(**_as_dict(data.get("llm"))),
            coverage=CoverageConfig(**_as_dict(data.get("coverage"))),
            generation=GenerationConfig(**_as_dict(data.get("generation"))),
            output=OutputConfig(**_as_dict(data.get("output"))),
        )
        config.validate()
        return config

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.to_dict(), sort_keys=False, allow_unicode=False)

    def validate(self) -> None:
        allowed_frameworks = {"auto", "flutter", "react"}
        if self.framework not in allowed_frameworks:
            raise ConfigValidationError(
                f"framework must be one of {sorted(allowed_frameworks)}, got: {self.framework}"
            )

        if not self.project_name.strip():
            raise ConfigValidationError("project_name cannot be empty")

        if not 0 <= self.llm.temperature <= 1:
            raise ConfigValidationError("llm.temperature must be between 0 and 1")

        if self.coverage.target < 1 or self.coverage.target > 100:
            raise ConfigValidationError("coverage.target must be between 1 and 100")

        if self.generation.max_files_per_run < 1:
            raise ConfigValidationError("generation.max_files_per_run must be >= 1")

        if self.generation.max_iterations < 1:
            raise ConfigValidationError("generation.max_iterations must be >= 1")

        if self.generation.write_mode not in {"overwrite", "append"}:
            raise ConfigValidationError("generation.write_mode must be 'overwrite' or 'append'")

        if not self.coverage.include:
            raise ConfigValidationError("coverage.include must contain at least one glob pattern")

        if not self.output.dashboard_path.strip():
            raise ConfigValidationError("output.dashboard_path cannot be empty")

        if not self.output.report_json_path.strip():
            raise ConfigValidationError("output.report_json_path cannot be empty")


class ConfigValidationError(ValueError):
    """Raised when sentinel.yaml has invalid structure or values."""


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}
