from __future__ import annotations

import asyncio
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from warlock_sentinel.adapters.flutter_adapter import FlutterAdapter
from warlock_sentinel.adapters.react_adapter import ReactAdapter
from warlock_sentinel.config import SentinelConfig
from warlock_sentinel.coverage.parser import CoverageParser, FileCoverage
from warlock_sentinel.generators.test_generator import TestGenerator
from warlock_sentinel.project_detector import ProjectInfo


async def run_autocuration_loop(
    project_info: ProjectInfo,
    config: SentinelConfig,
    console: Console,
    gemini_api_key: str | None = None,
    target_file: Path | None = None,
) -> None:
    adapter = _select_adapter(project_info)
    parser = CoverageParser()
    generator = TestGenerator(
        gemini_api_key=gemini_api_key or _resolve_api_key(config),
        model=config.llm.model,
    )

    project_root = project_info.root
    target = float(config.coverage.target)
    max_iterations = config.generation.max_iterations

    console.print(
        Panel.fit(
            f"Starting autocuration loop for [bold]{config.project_name}[/bold]\n"
            f"Framework: [cyan]{project_info.framework}[/cyan] | Target coverage: [green]{target:.1f}%[/green]",
            title="Warlock Sentinel",
        )
    )

    await asyncio.to_thread(adapter.prepare, config, project_info, project_root)

    for iteration in range(1, max_iterations + 1):
        console.print(f"\n[bold]Iteration {iteration}/{max_iterations}[/bold]")

        report = await asyncio.to_thread(parser.parse, project_info, str(project_root))
        current_coverage = report.total_coverage
        console.print(f"[cyan]Current coverage:[/cyan] {current_coverage:.2f}%")

        if current_coverage >= target:
            console.print(Panel.fit("Coverage target reached.", style="green", title="Success"))
            return

        low_files = [file for file in report.files if file.coverage < target and file.gaps]
        if target_file is not None:
            target_path = target_file if target_file.is_absolute() else project_root / target_file
            low_files = [
                file
                for file in low_files
                if _resolve_source_path(project_root=project_root, file_path=file.file_path) == target_path
            ]
        if not low_files:
            console.print(
                Panel.fit(
                    "No actionable uncovered lines found in coverage report.",
                    title="Stopped",
                    style="yellow",
                )
            )
            return

        selected = low_files[: config.generation.max_files_per_run]
        generated_files = await _generate_tests_for_files(
            adapter=adapter,
            generator=generator,
            config=config,
            project_info=project_info,
            project_root=project_root,
            file_coverages=selected,
            console=console,
        )

        if not generated_files:
            console.print(
                Panel.fit(
                    "No new tests were generated in this iteration.",
                    title="Stopped",
                    style="yellow",
                )
            )
            return

        with console.status("[cyan]Running focused validation and refreshing coverage...[/cyan]"):
            await asyncio.to_thread(adapter.run_fast_scan, config, project_info, project_root, generated_files)

        refreshed_report = await asyncio.to_thread(parser.parse, project_info, str(project_root))
        console.print(
            f"[cyan]Coverage after iteration {iteration}:[/cyan] {refreshed_report.total_coverage:.2f}%"
        )

        _render_iteration_summary(console, report, refreshed_report, target=target)

        if refreshed_report.total_coverage >= target:
            console.print(Panel.fit("Coverage target reached after test execution.", style="green"))
            return

    console.print(
        Panel.fit(
            "Max iterations reached before hitting target coverage.\n"
            "Review generated tests and run again.",
            title="Incomplete",
            style="yellow",
        )
    )


async def _generate_tests_for_files(
    adapter: FlutterAdapter | ReactAdapter,
    generator: TestGenerator,
    config: SentinelConfig,
    project_info: ProjectInfo,
    project_root: Path,
    file_coverages: list[FileCoverage],
    console: Console,
) -> list[Path]:
    generated_files: list[Path] = []

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    )

    with progress:
        task_id = progress.add_task("Generating tests", total=len(file_coverages))

        for file_coverage in file_coverages:
            source_path = _resolve_source_path(project_root=project_root, file_path=file_coverage.file_path)
            if not source_path.exists():
                progress.advance(task_id)
                continue

            test_code = await generator.generate_tests(
                project_info=project_info,
                file_path=str(source_path),
                coverage_gaps=file_coverage.gaps,
            )

            if not test_code.strip():
                progress.advance(task_id)
                continue

            target_test_path = adapter.test_path_for_source(project_root=project_root, source_file=source_path)
            await asyncio.to_thread(
                _write_test_code,
                path=target_test_path,
                content=test_code,
                write_mode=config.generation.write_mode,
            )

            validated_code = await _validate_and_repair_test(
                adapter=adapter,
                generator=generator,
                config=config,
                project_info=project_info,
                project_root=project_root,
                test_path=target_test_path,
                source_code=source_path.read_text(encoding="utf-8"),
                initial_code=test_code,
                console=console,
            )

            if validated_code != test_code:
                await asyncio.to_thread(_write_test_code, path=target_test_path, content=validated_code, write_mode="overwrite")

            generated_files.append(target_test_path)
            progress.advance(task_id)

    return generated_files


async def _validate_and_repair_test(
    adapter: FlutterAdapter | ReactAdapter,
    generator: TestGenerator,
    config: SentinelConfig,
    project_info: ProjectInfo,
    project_root: Path,
    test_path: Path,
    source_code: str,
    initial_code: str,
    console: Console,
) -> str:
    current_code = initial_code
    last_error = ""

    for attempt in range(1, 4):
        try:
            await asyncio.to_thread(
                adapter.run_single_test,
                test_path,
                config,
                project_info,
                project_root,
            )
            if attempt > 1:
                console.print(f"[green]Test repaired successfully[/green]: {test_path.name}")
            return current_code
        except Exception as error:
            last_error = str(error)
            console.print(f"[yellow]Validation failed ({attempt}/3)[/yellow] {test_path.name}")
            console.print(f"[dim]{last_error}[/dim]")
            if attempt == 3:
                break

            current_code = await generator.fix_test(
                project_info=project_info,
                file_path=str(test_path),
                source_code=source_code,
                failed_test_code=current_code,
                console_error=last_error,
            )

            await asyncio.to_thread(_write_test_code, path=test_path, content=current_code, write_mode="overwrite")

    console.print(f"[red]Unable to repair test after 3 attempts[/red]: {test_path.name}")
    if last_error:
        console.print(f"[dim]{last_error}[/dim]")
    return current_code


def _resolve_source_path(project_root: Path, file_path: str) -> Path:
    path = Path(file_path)
    if path.is_absolute():
        return path
    return project_root / path


def _write_test_code(path: Path, content: str, write_mode: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def _render_iteration_summary(
    console: Console,
    previous_report,
    refreshed_report,
    target: float,
) -> None:
    table = Table(title="Iteration Summary", show_lines=False)
    table.add_column("Archivo", style="cyan")
    table.add_column("Cobertura anterior", justify="right")
    table.add_column("Cobertura nueva", justify="right")
    table.add_column("Estado")

    refreshed_map = {file_cov.file_path: file_cov for file_cov in refreshed_report.files}

    for previous in previous_report.files:
        current = refreshed_map.get(previous.file_path)
        new_coverage = current.coverage if current else previous.coverage
        delta_state = _status_emoji(new_coverage)
        table.add_row(
            previous.file_path,
            f"{previous.coverage:.2f}%",
            f"{new_coverage:.2f}%",
            delta_state,
        )

    table.add_row(
        "Total",
        f"{previous_report.total_coverage:.2f}%",
        f"{refreshed_report.total_coverage:.2f}%",
        _status_emoji(refreshed_report.total_coverage if refreshed_report.total_coverage else target),
    )

    console.print(table)


def _status_emoji(coverage: float) -> str:
    if coverage < 50:
        return "🔴"
    if coverage < 80:
        return "🟡"
    return "🟢"


def _select_adapter(project_info: ProjectInfo) -> FlutterAdapter | ReactAdapter:
    if project_info.framework == "flutter":
        return FlutterAdapter()
    if project_info.framework == "react":
        return ReactAdapter()
    raise RuntimeError("Unsupported framework for autocuration loop")


def _resolve_api_key(config: SentinelConfig) -> str | None:
    import os

    if config.llm.api_key_env:
        env_value = os.getenv(config.llm.api_key_env)
        if env_value:
            return env_value
    return None
