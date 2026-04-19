from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Literal

FrameworkName = Literal["flutter", "react", "unknown"]


@dataclass(slots=True)
class ProjectInfo:
    root: Path
    framework: FrameworkName
    language: str
    package_manager: str | None
    stacks: list[str]
    metadata: dict[str, str]


@dataclass(slots=True)
class ProjectDetector:
    """Detect supported framework and stack signals from repository markers."""

    def detect(self, project_root: Path) -> ProjectInfo:
        if (project_root / "pubspec.yaml").exists():
            return self._detect_flutter(project_root)

        if (project_root / "package.json").exists():
            return self._detect_react(project_root)

        return ProjectInfo(
            root=project_root,
            framework="unknown",
            language="unknown",
            package_manager=self._detect_package_manager(project_root),
            stacks=[],
            metadata={},
        )

    def _detect_flutter(self, project_root: Path) -> ProjectInfo:
        pubspec_text = (project_root / "pubspec.yaml").read_text(encoding="utf-8")
        stacks: list[str] = []
        metadata: dict[str, str] = {}

        if "flutter_riverpod" in pubspec_text or "hooks_riverpod" in pubspec_text:
            stacks.append("riverpod")

        if "supabase_flutter" in pubspec_text:
            stacks.append("supabase")

        if "bloc" in pubspec_text:
            stacks.append("bloc")

        metadata["has_integration_test"] = str((project_root / "integration_test").exists()).lower()
        metadata["has_unit_test"] = str((project_root / "test").exists()).lower()

        return ProjectInfo(
            root=project_root,
            framework="flutter",
            language="dart",
            package_manager="pub",
            stacks=stacks,
            metadata=metadata,
        )

    def _detect_react(self, project_root: Path) -> ProjectInfo:
        package_json_path = project_root / "package.json"
        package_data = self._load_package_json(package_json_path)
        deps = self._collect_dependencies(package_data)

        stacks: list[str] = []
        metadata: dict[str, str] = {}

        framework: FrameworkName = "react"
        if "next" in deps:
            stacks.append("nextjs")

        if "@supabase/supabase-js" in deps:
            stacks.append("supabase")

        if "@tanstack/react-query" in deps:
            stacks.append("react-query")

        if "redux" in deps or "@reduxjs/toolkit" in deps:
            stacks.append("redux")

        if "zustand" in deps:
            stacks.append("zustand")

        if "typescript" in deps or (project_root / "tsconfig.json").exists():
            language = "typescript"
        else:
            language = "javascript"

        metadata["has_src"] = str((project_root / "src").exists()).lower()
        metadata["has_app_router"] = str((project_root / "app").exists()).lower()

        return ProjectInfo(
            root=project_root,
            framework=framework,
            language=language,
            package_manager=self._detect_package_manager(project_root),
            stacks=stacks,
            metadata=metadata,
        )

    def _detect_package_manager(self, project_root: Path) -> str | None:
        if (project_root / "pnpm-lock.yaml").exists():
            return "pnpm"
        if (project_root / "yarn.lock").exists():
            return "yarn"
        if (project_root / "bun.lockb").exists() or (project_root / "bun.lock").exists():
            return "bun"
        if (project_root / "package-lock.json").exists():
            return "npm"
        return None

    def _load_package_json(self, path: Path) -> dict[str, object]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _collect_dependencies(self, package_data: dict[str, object]) -> set[str]:
        deps: set[str] = set()
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            values = package_data.get(key)
            if isinstance(values, dict):
                deps.update(str(name) for name in values.keys())
        return deps
