from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from warlock_sentinel.config import SentinelConfig
from warlock_sentinel.project_detector import ProjectInfo


class BaseAdapter(ABC):
    """Framework contract used by the autocuration loop."""

    framework_name: str

    @abstractmethod
    def prepare(self, config: SentinelConfig, project: ProjectInfo, project_root: Path) -> None:
        """Validate local prerequisites and initialize runtime context."""

    @abstractmethod
    def collect_coverage_targets(
        self,
        config: SentinelConfig,
        project: ProjectInfo,
        project_root: Path,
    ) -> list[Path]:
        """Collect source files that can receive generated tests."""

    @abstractmethod
    def test_path_for_source(self, project_root: Path, source_file: Path) -> Path:
        """Return the output test path for a given source file."""

    @abstractmethod
    def run_tests(self, config: SentinelConfig, project: ProjectInfo, project_root: Path) -> None:
        """Execute framework tests with coverage enabled."""

    @abstractmethod
    def coverage_paths(self, project_root: Path) -> list[Path]:
        """Return coverage report file paths used by the parser."""
