from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from warlock_sentinel.adapters.base import BaseAdapter
from warlock_sentinel.config import SentinelConfig
from warlock_sentinel.project_detector import ProjectInfo


class ReactAdapter(BaseAdapter):
    framework_name = "react"

    def prepare(self, config: SentinelConfig, project: ProjectInfo, project_root: Path) -> None:
        if project.framework != "react":
            raise RuntimeError("ReactAdapter received non-React project info")

        if not (project_root / "package.json").exists():
            raise RuntimeError("package.json not found in project root")

        manager = project.package_manager
        if manager is None and shutil.which("npm") is None:
            raise RuntimeError("No JavaScript package manager detected")

        test_root = project_root / "src" / "__tests__"
        test_root.mkdir(parents=True, exist_ok=True)

    def collect_coverage_targets(
        self,
        config: SentinelConfig,
        project: ProjectInfo,
        project_root: Path,
    ) -> list[Path]:
        candidates: list[Path] = []
        valid_suffixes = {".ts", ".tsx", ".js", ".jsx"}

        for pattern in config.coverage.include:
            for path in project_root.glob(pattern):
                if not path.is_file() or path.suffix not in valid_suffixes:
                    continue
                if path.name.endswith(".test.ts") or path.name.endswith(".test.tsx"):
                    continue
                if path.name.endswith(".spec.ts") or path.name.endswith(".spec.tsx"):
                    continue
                if self._is_excluded(path, project_root, config.coverage.exclude):
                    continue
                candidates.append(path)

        return sorted(set(candidates))

    def test_path_for_source(self, project_root: Path, source_file: Path) -> Path:
        relative = source_file.relative_to(project_root)

        if relative.parts and relative.parts[0] in {"src", "app"}:
            tail = Path(*relative.parts[1:]) if len(relative.parts) > 1 else Path(relative.name)
            test_rel = Path("src") / "__tests__" / tail
        else:
            test_rel = Path("src") / "__tests__" / relative

        suffix = ".test.tsx" if source_file.suffix in {".tsx", ".jsx"} else ".test.ts"
        return project_root / test_rel.with_suffix(suffix)

    def run_tests(self, config: SentinelConfig, project: ProjectInfo, project_root: Path) -> None:
        command = self._test_command(project)
        completed = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            error_text = completed.stderr.strip() or completed.stdout.strip() or "Unknown JS test error"
            raise RuntimeError(self.clean_error_output(error_text))

    def run_fast_scan(
        self,
        config: SentinelConfig,
        project: ProjectInfo,
        project_root: Path,
        changed_files: list[Path] | None = None,
    ) -> None:
        if changed_files:
            for file_path in changed_files:
                self.run_single_test(file_path, config, project, project_root)
            return
        self.run_tests(config, project, project_root)

    def run_single_test(
        self,
        test_path: Path,
        config: SentinelConfig,
        project: ProjectInfo,
        project_root: Path,
        command_args: list[str] | None = None,
    ) -> None:
        manager = project.package_manager or "npm"
        if manager == "pnpm":
            command = ["pnpm", "test", "--", str(test_path), "--coverage"]
        elif manager == "yarn":
            command = ["yarn", "test", str(test_path), "--coverage"]
        elif manager == "bun":
            command = ["bun", "test", str(test_path), "--coverage"]
        else:
            command = ["npm", "test", "--", str(test_path), "--coverage"]

        if command_args:
            command.extend(command_args)

        completed = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            error_text = completed.stderr.strip() or completed.stdout.strip() or "Unknown JS single test error"
            raise RuntimeError(self.clean_error_output(error_text))

    def coverage_paths(self, project_root: Path) -> list[Path]:
        return [
            project_root / "coverage" / "coverage-final.json",
            project_root / "coverage" / "lcov.info",
        ]

    def _is_excluded(self, path: Path, project_root: Path, excludes: list[str]) -> bool:
        relative = path.relative_to(project_root)
        return any(relative.match(pattern) for pattern in excludes)

    def _test_command(self, project: ProjectInfo) -> list[str]:
        manager = project.package_manager or "npm"
        if manager == "pnpm":
            return ["pnpm", "test", "--", "--coverage"]
        if manager == "yarn":
            return ["yarn", "test", "--coverage"]
        if manager == "bun":
            return ["bun", "test", "--coverage"]
        return ["npm", "test", "--", "--coverage"]
