from __future__ import annotations

import asyncio
from dataclasses import replace
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from warlock_sentinel.config import ConfigValidationError, SentinelConfig
from warlock_sentinel.core.loop import run_autocuration_loop
from warlock_sentinel.coverage.parser import CoverageParser
from warlock_sentinel.dashboard.generator import DashboardGenerator
from warlock_sentinel.project_detector import ProjectDetector

app = typer.Typer(
    add_completion=False,
    help=(
        "Warlock Sentinel: AI testing agent for Flutter and React/Next.js. "
        "Run `warlock init` once, then execute `warlock` in your target repository."
    ),
)
console = Console()


@app.command()
def init(force: bool = typer.Option(False, "--force", help="Overwrite existing sentinel.yaml")) -> None:
    """Create sentinel.yaml from sentinel.yaml.example when available."""
    project_root = Path.cwd()
    config_path = project_root / "sentinel.yaml"
    if config_path.exists() and not force:
        console.print("[yellow]sentinel.yaml already exists. Use --force to overwrite.[/yellow]")
        raise typer.Exit(code=0)

    example_path = project_root / "sentinel.yaml.example"
    if example_path.exists():
        content = example_path.read_text(encoding="utf-8")
    else:
        content = SentinelConfig.defaults(project_name=project_root.name).to_yaml()

    config_path.write_text(content, encoding="utf-8")
    console.print(f"[green]Created[/green] {config_path}")


@app.command()
def dashboard(
    framework: str = typer.Option("auto", "--framework", help="Framework override: auto | flutter | react"),
    output: str | None = typer.Option(None, "--output", help="Output HTML path override"),
) -> None:
    """Generate only the HTML dashboard from existing coverage reports."""
    project_root = Path.cwd()
    project_info = _detect_project(framework=framework, project_root=project_root)
    config = _load_config(project_root)

    parser = CoverageParser()
    report = parser.parse(project_info=project_info, project_root=str(project_root))

    if not report.files:
        console.print("[yellow]No coverage report data found. Run tests with coverage first.[/yellow]")
        raise typer.Exit(code=1)

    generator = DashboardGenerator()
    output_path = Path(output) if output else project_root / config.output.dashboard_path
    written = generator.generate(
        report=report,
        output_path=output_path,
        project_name=config.project_name,
        rerun_command="warlock",
    )
    console.print(Panel.fit(f"Dashboard generated at:\n{written}", title="Dashboard", style="green"))


@app.callback(invoke_without_command=True)
def run(
    ctx: typer.Context,
    target: int = typer.Option(85, "--target", min=1, max=100, help="Target coverage percentage"),
    max_iterations: int = typer.Option(
        6,
        "--max-iterations",
        min=1,
        max=50,
        help="Maximum number of autocuration iterations",
    ),
    framework: str = typer.Option(
        "auto",
        "--framework",
        help="Framework override: auto | flutter | react",
    ),
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        help="Gemini API key. If omitted, uses GEMINI_API_KEY or configured env var.",
    ),
) -> None:
    """Run the full autocuration loop when no subcommand is provided."""
    if ctx.invoked_subcommand is not None:
        return

    project_root = Path.cwd()
    project_info = _detect_project(framework=framework, project_root=project_root)
    config = _load_config(project_root)

    config.coverage.target = target
    config.generation.max_iterations = max_iterations

    resolved_api_key = _resolve_api_key(api_key=api_key, config=config)

    if project_info.framework == "unknown":
        console.print("[yellow]No supported framework detected (Flutter or React/Next.js).[/yellow]")
        raise typer.Exit(code=1)

    try:
        asyncio.run(
            run_autocuration_loop(
                project_info=project_info,
                config=config,
                console=console,
                gemini_api_key=resolved_api_key,
            )
        )
    except RuntimeError as error:
        console.print(f"[red]Autocuration failed:[/red] {error}")
        raise typer.Exit(code=3) from error


def _detect_project(framework: str, project_root: Path):
    detector = ProjectDetector()
    project_info = detector.detect(project_root)

    if framework != "auto":
        if framework not in {"flutter", "react"}:
            console.print("[red]Invalid --framework value. Use auto, flutter, or react.[/red]")
            raise typer.Exit(code=2)
        project_info = replace(project_info, framework=framework)

    return project_info


def _load_config(project_root: Path) -> SentinelConfig:
    try:
        config = SentinelConfig.load(project_root / "sentinel.yaml")
    except ConfigValidationError as error:
        console.print(f"[red]Invalid sentinel.yaml:[/red] {error}")
        raise typer.Exit(code=2) from error

    if config is None:
        return SentinelConfig.defaults(project_name=project_root.name)
    return config


def _resolve_api_key(api_key: str | None, config: SentinelConfig) -> str | None:
    if api_key:
        return api_key

    default_env_key = os.getenv("GEMINI_API_KEY")
    if default_env_key:
        return default_env_key

    if config.llm.api_key_env:
        return os.getenv(config.llm.api_key_env)

    return None
