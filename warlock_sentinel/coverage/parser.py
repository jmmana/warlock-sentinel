from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from warlock_sentinel.project_detector import ProjectInfo


@dataclass(slots=True)
class CoverageGap:
    file_path: str
    line_start: int
    line_end: int
    missed_lines: list[int]


@dataclass(slots=True)
class FileCoverage:
    file_path: str
    total_lines: int
    covered_lines: int
    coverage: float
    gaps: list[CoverageGap]


@dataclass(slots=True)
class CoverageReport:
    total_coverage: float
    files: list[FileCoverage]


class CoverageParser:
    def parse_flutter_coverage(self, project_root: str) -> CoverageReport:
        root = Path(project_root)
        lcov_path = root / "coverage" / "lcov.info"
        if not lcov_path.exists():
            return CoverageReport(total_coverage=0.0, files=[])
        return self._parse_lcov(lcov_path=lcov_path, project_root=root)

    def parse_react_coverage(self, project_root: str) -> CoverageReport:
        root = Path(project_root)
        json_path = root / "coverage" / "coverage-final.json"
        lcov_path = root / "coverage" / "lcov.info"

        if json_path.exists():
            report = self._parse_istanbul_json(json_path=json_path, project_root=root)
            if report.files:
                return report

        if lcov_path.exists():
            return self._parse_lcov(lcov_path=lcov_path, project_root=root)

        return CoverageReport(total_coverage=0.0, files=[])

    def parse(self, project_info: ProjectInfo, project_root: str) -> CoverageReport:
        if project_info.framework == "flutter":
            return self.parse_flutter_coverage(project_root)
        if project_info.framework == "react":
            return self.parse_react_coverage(project_root)
        return CoverageReport(total_coverage=0.0, files=[])

    def _parse_lcov(self, lcov_path: Path, project_root: Path) -> CoverageReport:
        files: list[FileCoverage] = []
        current_path: Path | None = None
        line_hits: dict[int, int] = {}

        for raw_line in lcov_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line.startswith("SF:"):
                self._flush_lcov_file(files=files, project_root=project_root, path=current_path, hits=line_hits)
                current_path = Path(line.removeprefix("SF:"))
                line_hits = {}
                continue

            if line.startswith("DA:"):
                payload = line.removeprefix("DA:")
                parts = payload.split(",")
                if len(parts) >= 2:
                    try:
                        row = int(parts[0])
                        hit_count = int(parts[1])
                    except ValueError:
                        continue
                    line_hits[row] = hit_count
                continue

            if line == "end_of_record":
                self._flush_lcov_file(files=files, project_root=project_root, path=current_path, hits=line_hits)
                current_path = None
                line_hits = {}

        self._flush_lcov_file(files=files, project_root=project_root, path=current_path, hits=line_hits)
        return self._build_report(files)

    def _flush_lcov_file(
        self,
        files: list[FileCoverage],
        project_root: Path,
        path: Path | None,
        hits: dict[int, int],
    ) -> None:
        if path is None:
            return

        total_lines = len(hits)
        if total_lines == 0:
            return

        covered_lines = sum(1 for count in hits.values() if count > 0)
        missed = sorted(line for line, count in hits.items() if count == 0)

        normalized = self._normalize_path(path=path, project_root=project_root)
        gaps = self._gaps_from_lines(file_path=normalized, missed_lines=missed)
        coverage = self._safe_percent(covered_lines, total_lines)

        files.append(
            FileCoverage(
                file_path=normalized,
                total_lines=total_lines,
                covered_lines=covered_lines,
                coverage=coverage,
                gaps=gaps,
            )
        )

    def _parse_istanbul_json(self, json_path: Path, project_root: Path) -> CoverageReport:
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return CoverageReport(total_coverage=0.0, files=[])

        files: list[FileCoverage] = []
        if not isinstance(payload, dict):
            return CoverageReport(total_coverage=0.0, files=[])

        for raw_path, item in payload.items():
            if not isinstance(raw_path, str) or not isinstance(item, dict):
                continue

            statement_hits = item.get("s")
            statement_map = item.get("statementMap")
            if not isinstance(statement_hits, dict) or not isinstance(statement_map, dict):
                continue

            total = 0
            covered = 0
            missed_lines: set[int] = set()

            for statement_id, hit in statement_hits.items():
                if statement_id not in statement_map:
                    continue
                loc = statement_map.get(statement_id)
                if not isinstance(loc, dict):
                    continue

                total += 1
                hit_count = int(hit) if isinstance(hit, (int, float)) else 0
                if hit_count > 0:
                    covered += 1
                    continue

                start_line = self._extract_nested_int(loc, "start", "line")
                end_line = self._extract_nested_int(loc, "end", "line")
                if start_line is None or end_line is None:
                    continue
                for line_number in range(start_line, end_line + 1):
                    missed_lines.add(line_number)

            if total == 0:
                continue

            normalized = self._normalize_path(path=Path(raw_path), project_root=project_root)
            coverage = self._safe_percent(covered, total)
            missed = sorted(missed_lines)
            files.append(
                FileCoverage(
                    file_path=normalized,
                    total_lines=total,
                    covered_lines=covered,
                    coverage=coverage,
                    gaps=self._gaps_from_lines(file_path=normalized, missed_lines=missed),
                )
            )

        return self._build_report(files)

    def _build_report(self, files: list[FileCoverage]) -> CoverageReport:
        if not files:
            return CoverageReport(total_coverage=0.0, files=[])

        total_lines = sum(item.total_lines for item in files)
        covered_lines = sum(item.covered_lines for item in files)
        overall = self._safe_percent(covered_lines, total_lines)
        return CoverageReport(total_coverage=overall, files=sorted(files, key=lambda item: item.coverage))

    def _gaps_from_lines(self, file_path: str, missed_lines: list[int]) -> list[CoverageGap]:
        if not missed_lines:
            return []

        groups: list[list[int]] = []
        current: list[int] = []
        for line in missed_lines:
            if not current or line == current[-1] + 1:
                current.append(line)
            else:
                groups.append(current)
                current = [line]
        if current:
            groups.append(current)

        return [
            CoverageGap(
                file_path=file_path,
                line_start=chunk[0],
                line_end=chunk[-1],
                missed_lines=chunk,
            )
            for chunk in groups
        ]

    def _normalize_path(self, path: Path, project_root: Path) -> str:
        if path.is_absolute():
            try:
                return path.relative_to(project_root).as_posix()
            except ValueError:
                return path.as_posix()
        return path.as_posix()

    def _safe_percent(self, covered: int, total: int) -> float:
        if total <= 0:
            return 0.0
        return round((covered / total) * 100, 2)

    def _extract_nested_int(self, source: dict[str, object], key: str, nested_key: str) -> int | None:
        nested = source.get(key)
        if not isinstance(nested, dict):
            return None
        value = nested.get(nested_key)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        return None
