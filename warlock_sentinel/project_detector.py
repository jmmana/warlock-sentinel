from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Literal

FrameworkName = Literal["flutter", "react", "angular", "csharp", "unknown"]


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
        if self._has_any(project_root, ["**/*.csproj", "**/*.sln"]):
            return self._detect_csharp(project_root)

        if (project_root / "pubspec.yaml").exists():
            return self._detect_flutter(project_root)

        if self._has_any(project_root, ["**/angular.json", "**/nx.json"]):
            return self._detect_angular(project_root)

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

    def _detect_angular(self, project_root: Path) -> ProjectInfo:
        package_json_path = project_root / "package.json"
        package_data = self._load_package_json(package_json_path) if package_json_path.exists() else {}
        deps = self._collect_dependencies(package_data)

        stacks: list[str] = []
        metadata: dict[str, str] = {}

        if "@supabase/supabase-js" in deps:
            stacks.append("supabase")

        if "@ngrx/store" in deps or "@ngrx/effects" in deps:
            stacks.append("ngrx")

        metadata["has_src"] = str((project_root / "src").exists()).lower()
        metadata["has_app"] = str((project_root / "app").exists()).lower()
        metadata["has_angular_json"] = str(self._has_any(project_root, ["**/angular.json"])).lower()
        metadata["has_nx_json"] = str(self._has_any(project_root, ["**/nx.json"])).lower()

        return ProjectInfo(
            root=project_root,
            framework="angular",
            language="typescript",
            package_manager=self._detect_package_manager(project_root),
            stacks=stacks,
            metadata=metadata,
        )

    def _detect_csharp(self, project_root: Path) -> ProjectInfo:
        project_files = [*project_root.glob("**/*.csproj"), *project_root.glob("**/*.sln")]
        stacks: list[str] = []
        metadata: dict[str, str] = {}

        project_text = "\n".join(self._safe_read_text(path) for path in project_files)
        if "Supabase" in project_text:
            stacks.append("supabase")
        if "Microsoft.EntityFrameworkCore" in project_text:
            stacks.append("entity-framework")
        if "Moq" in project_text:
            stacks.append("moq")

        metadata["has_solution"] = str(any(path.suffix == ".sln" for path in project_files)).lower()
        metadata["project_file_count"] = str(len(project_files))

        return ProjectInfo(
            root=project_root,
            framework="csharp",
            language="csharp",
            package_manager=None,
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

        if "vue" in deps or "@vue/runtime-core" in deps:
            stacks.append("vue")

        if "@nestjs/core" in deps or "@nestjs/common" in deps:
            stacks.append("nestjs")

        if "@supabase/supabase-js" in deps:
            stacks.append("supabase")

        if "@tanstack/react-query" in deps:
            stacks.append("react-query")

        if "redux" in deps or "@reduxjs/toolkit" in deps:
            stacks.append("redux")

        if "zustand" in deps:
            stacks.append("zustand")

        if "pinia" in deps or "vuex" in deps:
            stacks.append("pinia")

        if "typescript" in deps or (project_root / "tsconfig.json").exists():
            language = "typescript"
        else:
            language = "javascript"

        metadata["has_src"] = str((project_root / "src").exists()).lower()
        metadata["has_app_router"] = str((project_root / "app").exists()).lower()
        metadata["is_vue_project"] = str("vue" in stacks).lower()
        metadata["is_nest_project"] = str("nestjs" in stacks).lower()

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

    def _has_any(self, project_root: Path, patterns: list[str]) -> bool:
        return any(any(project_root.glob(pattern)) for pattern in patterns)

    def _safe_read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return ""
