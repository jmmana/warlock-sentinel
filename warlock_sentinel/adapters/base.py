from __future__ import annotations

from abc import ABC, abstractmethod
import re
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

    def run_fast_scan(
        self,
        config: SentinelConfig,
        project: ProjectInfo,
        project_root: Path,
        changed_files: list[Path] | None = None,
    ) -> None:
        """Run a narrower coverage/test pass for recently generated or changed files."""
        self.run_tests(config=config, project=project, project_root=project_root)

    def clean_error_output(self, error_output: str) -> str:
        """Extract the most relevant error lines from noisy framework output."""
        lines = [line.strip() for line in error_output.splitlines() if line.strip()]
        relevant_patterns = [
            re.compile(r"Expected:|Actual:|TypeError|TypeError:\s|Exception|Error:", re.IGNORECASE),
            re.compile(r"AssertionError|Failed assertion|NoSuchMethodError|ReferenceError|SyntaxError", re.IGNORECASE),
            re.compile(r"FAILED\s+\(|FAIL\s+", re.IGNORECASE),
        ]

        relevant: list[str] = []
        for line in lines:
            if any(pattern.search(line) for pattern in relevant_patterns):
                relevant.append(line)

        if relevant:
            return "\n".join(dict.fromkeys(relevant))

        for line in reversed(lines):
            if len(line) > 12:
                return line

        return error_output.strip()

    @abstractmethod
    def run_single_test(
        self,
        test_path: Path,
        config: SentinelConfig,
        project: ProjectInfo,
        project_root: Path,
    ) -> None:
        """Execute one generated test file to validate it immediately."""

    @abstractmethod
    def coverage_paths(self, project_root: Path) -> list[Path]:
        """Return coverage report file paths used by the parser."""
