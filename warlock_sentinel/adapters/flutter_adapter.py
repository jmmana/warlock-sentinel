from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from warlock_sentinel.adapters.base import BaseAdapter
from warlock_sentinel.config import SentinelConfig
from warlock_sentinel.project_detector import ProjectInfo


class FlutterAdapter(BaseAdapter):
    framework_name = "flutter"

    def prepare(self, config: SentinelConfig, project: ProjectInfo, project_root: Path) -> None:
        if project.framework != "flutter":
            raise RuntimeError("FlutterAdapter received non-Flutter project info")

        if not (project_root / "pubspec.yaml").exists():
            raise RuntimeError("pubspec.yaml not found in project root")

        if shutil.which("flutter") is None:
            raise RuntimeError("Flutter SDK is not available in PATH")

        (project_root / "test").mkdir(parents=True, exist_ok=True)

    def collect_coverage_targets(
        self,
        config: SentinelConfig,
        project: ProjectInfo,
        project_root: Path,
    ) -> list[Path]:
        candidates: list[Path] = []
        for pattern in config.coverage.include:
            for path in project_root.glob(pattern):
                if not path.is_file() or path.suffix != ".dart":
                    continue
                if path.name.endswith("_test.dart"):
                    continue
                if self._is_excluded(path, project_root, config.coverage.exclude):
                    continue
                candidates.append(path)

        return sorted(set(candidates))

    def test_path_for_source(self, project_root: Path, source_file: Path) -> Path:
        relative = source_file.relative_to(project_root)
        if relative.parts and relative.parts[0] == "lib":
            target_rel = Path("test") / relative.relative_to("lib")
        else:
            target_rel = Path("test") / relative
        return project_root / target_rel.with_name(f"{source_file.stem}_test.dart")

    def run_tests(self, config: SentinelConfig, project: ProjectInfo, project_root: Path) -> None:
        command = ["flutter", "test", "--coverage"]
        completed = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            error_text = completed.stderr.strip() or completed.stdout.strip() or "Unknown flutter test error"
            raise RuntimeError(f"Flutter tests failed: {error_text}")

    def coverage_paths(self, project_root: Path) -> list[Path]:
        return [project_root / "coverage" / "lcov.info"]

    def _is_excluded(self, path: Path, project_root: Path, excludes: list[str]) -> bool:
        relative = path.relative_to(project_root)
        return any(relative.match(pattern) for pattern in excludes)
