from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Literal

from warlock_sentinel.coverage.parser import CoverageReport, FileCoverage

StatusColor = Literal["red", "yellow", "green"]


@dataclass(slots=True)
class ModuleSummary:
    name: str
    coverage: float
    files: list[FileCoverage]


class DashboardGenerator:
    """Generate a hierarchical HTML quality dashboard grouped by modules."""

    def generate(
        self,
        report: CoverageReport,
        output_path: Path,
        project_name: str,
        rerun_command: str = "warlock",
    ) -> Path:
    if output_path.as_posix().endswith("."):
      output_path = self.default_output_path(Path.cwd())
    output_path.parent.mkdir(parents=True, exist_ok=True)

        modules = self._group_by_module(report.files)
        health_score = self._weighted_health_score(report.files)
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        module_cards = "\n".join(self._render_module_card(mod) for mod in modules)

        html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Warlock Sentinel - Quality Report</title>
  <script src=\"https://cdn.tailwindcss.com\"></script>
</head>
<body class=\"bg-slate-950 text-slate-100 min-h-screen\">
  <div class=\"max-w-7xl mx-auto px-4 md:px-8 py-8\">
    <header class=\"mb-8 p-6 rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-950\">
      <div class=\"flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6\">
        <div>
          <p class=\"text-sky-400 uppercase tracking-widest text-xs\">Warlock Sentinel</p>
          <h1 class=\"text-3xl md:text-4xl font-extrabold mt-2\">Warlock Sentinel - Quality Report</h1>
          <p class=\"text-slate-300 mt-3\">Proyecto: <span class=\"font-semibold\">{self._escape(project_name)}</span></p>
          <p class=\"text-slate-400 text-sm mt-1\">Generado: {self._escape(generated_at)}</p>
        </div>
        <div class="flex flex-col gap-3 w-full lg:w-auto">
          <button
            id=\"rerun-warlock\"
            class="w-full lg:w-auto bg-sky-500 hover:bg-sky-400 text-slate-950 font-extrabold px-7 py-4 rounded-xl shadow-xl shadow-sky-900/40 transition text-base"
          >
            Re-ejecutar Warlock ahora
          </button>
          <p class=\"text-xs text-slate-400\">Comando sugerido: <span class=\"font-mono\">{self._escape(rerun_command)}</span></p>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-4 flex items-center gap-4">
          <div class="relative w-24 h-24 rounded-full border-4 border-slate-700 grid place-items-center">
            <div class="absolute inset-1 rounded-full bg-slate-950/80"></div>
            <div class="relative text-center">
              <p class="text-xs text-slate-400">Health</p>
              <p class="text-2xl font-extrabold {self._score_color_class(health_score)}">{health_score:.0f}</p>
            </div>
          </div>
          <div>
            <p class="text-slate-400 text-sm">Global Health Score</p>
            <p class="text-3xl font-extrabold {self._score_color_class(health_score)}">{health_score:.2f}%</p>
          </div>
        </div>
        <div class=\"rounded-xl border border-slate-800 bg-slate-900/60 p-4\">
          <p class=\"text-slate-400 text-sm\">Coverage General</p>
          <p class=\"text-4xl font-extrabold {self._score_color_class(report.total_coverage)}\">{report.total_coverage:.2f}%</p>
        </div>
        <div class=\"rounded-xl border border-slate-800 bg-slate-900/60 p-4\">
          <p class=\"text-slate-400 text-sm\">Archivos Analizados</p>
          <p class=\"text-4xl font-extrabold text-slate-100\">{len(report.files)}</p>
        </div>
      </div>
    </header>

    <main class=\"space-y-4\">
      {module_cards or '<div class="rounded-xl border border-slate-800 bg-slate-900 p-6 text-slate-300">No hay datos de coverage disponibles.</div>'}
    </main>
  </div>

  <script>
    document.querySelectorAll('[data-accordion-toggle]').forEach((button) => {{
      button.addEventListener('click', () => {{
        const targetId = button.getAttribute('data-accordion-toggle');
        const section = document.getElementById(targetId);
        const chevron = button.querySelector('[data-chevron]');
        if (!section || !chevron) return;
        const isHidden = section.classList.contains('hidden');
        if (isHidden) {{
          section.classList.remove('hidden');
          chevron.textContent = '▾';
        }} else {{
          section.classList.add('hidden');
          chevron.textContent = '▸';
        }}
      }});
    }});

    const rerunButton = document.getElementById('rerun-warlock');
    if (rerunButton) {{
      rerunButton.addEventListener('click', () => {{
        const cmd = {self._js_string(rerun_command)};
        const encoded = encodeURIComponent(cmd);
        window.location.href = `?run=${{encoded}}`;
        alert(`Ejecuta en tu terminal: ${{cmd}}`);
      }});
    }}
  </script>
</body>
</html>
"""

        output_path.write_text(html, encoding="utf-8")
        return output_path

    def default_output_path(self, project_root: Path) -> Path:
        return project_root / "coverage" / "warlock-dashboard.html"

    def _group_by_module(self, files: list[FileCoverage]) -> list[ModuleSummary]:
        grouped: dict[str, list[FileCoverage]] = {}
        for file_cov in files:
            module = self._module_name(file_cov.file_path)
            grouped.setdefault(module, []).append(file_cov)

        modules: list[ModuleSummary] = []
        for name, module_files in grouped.items():
            modules.append(
                ModuleSummary(
                    name=name,
                    coverage=self._weighted_health_score(module_files),
                    files=sorted(module_files, key=lambda item: item.coverage),
                )
                    <main class="space-y-4">
                      <section class="mb-2">
                        <h2 class="text-2xl font-bold">Módulos del Proyecto</h2>
                        <p class="text-slate-400 text-sm">Haz click en cada módulo para expandir y ver el detalle por archivo.</p>
                      </section>

        return sorted(modules, key=lambda module: module.coverage)

    def _module_name(self, file_path: str) -> str:
        path = PurePosixPath(file_path)
        parts = [part for part in path.parts if part not in {".", ""}]
        if not parts:
            return "root/"

        if len(parts) >= 2 and parts[0] in {"src", "lib", "app"}:
            return f"{parts[0]}/{parts[1]}/"

        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}/"

        return f"{parts[0]}/"

    def _weighted_health_score(self, files: list[FileCoverage]) -> float:
        total_weight = 0
        weighted_score = 0.0
        for item in files:
            weight = max(item.total_lines, 1)
            total_weight += weight
            weighted_score += item.coverage * weight
        if total_weight == 0:
            return 0.0
        return round(weighted_score / total_weight, 2)

    def _render_module_card(self, module: ModuleSummary) -> str:
        status = self._status(module.coverage)
        progress = self._progress_bar(module.coverage)
        module_id = f"module-{abs(hash(module.name))}"
        file_rows = "\n".join(self._render_file_row(file_cov) for file_cov in module.files)

        return f"""
<section class=\"rounded-2xl border border-slate-800 bg-slate-900/80 overflow-hidden\">
  <button data-accordion-toggle=\"{module_id}\" class=\"w-full text-left p-5 hover:bg-slate-800/50 transition\">
    <div class=\"flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4\">
      <div>
        <p class=\"text-slate-300 text-sm\">Módulo</p>
        <h2 class=\"text-xl font-bold\">{self._escape(module.name)}</h2>
      </div>
      <div class=\"flex flex-wrap items-center gap-3 text-sm\">
        <span class=\"px-2 py-1 rounded-md border border-slate-700\">Archivos: {len(module.files)}</span>
        <span class=\"px-2 py-1 rounded-md border border-slate-700\">Promedio: {module.coverage:.2f}%</span>
        <span class=\"text-xl\">{status['emoji']}</span>
        <span data-chevron class=\"text-xl text-slate-400\">▸</span>
      </div>
    </div>
    <div class=\"mt-4\">{progress}</div>
  </button>

  <div id=\"{module_id}\" class=\"hidden border-t border-slate-800\">
    <div class=\"p-4 space-y-3\">{file_rows}</div>
  </div>
</section>
""".strip()

    def _render_file_row(self, file_cov: FileCoverage) -> str:
        status = self._status(file_cov.coverage)
        progress = self._progress_bar(file_cov.coverage, compact=True)
        file_name = PurePosixPath(file_cov.file_path).name

        return f"""
<div class=\"rounded-xl border border-slate-800 bg-slate-950/70 p-3\">
  <div class=\"flex flex-col md:flex-row md:items-center md:justify-between gap-2\">
    <p class=\"font-mono text-xs text-slate-300\" title=\"{self._escape(file_cov.file_path)}\">{self._escape(file_name)}</p>
    <div class=\"flex items-center gap-2\">
      <span class=\"text-lg\">{status['emoji']}</span>
      <span class=\"text-sm font-semibold {status['text_class']}\">{file_cov.coverage:.2f}%</span>
    </div>
  </div>
  <div class=\"mt-2\">{progress}</div>
</div>
""".strip()

    def _progress_bar(self, value: float, compact: bool = False) -> str:
        status = self._status(value)
        height = "h-3" if compact else "h-4"
        return (
            f"<div class=\"w-full bg-slate-800 rounded-full overflow-hidden {height}\">"
            f"<div class=\"{status['bar_class']} {height}\" style=\"width:{max(0.0, min(100.0, value)):.2f}%\"></div>"
            "</div>"
        )

    def _status(self, coverage: float) -> dict[str, str]:
        if coverage < 50:
            return {
                "emoji": "🔴",
                "bar_class": "bg-red-500",
                "text_class": "text-red-400",
            }
        if coverage < 80:
            return {
                "emoji": "🟡",
                "bar_class": "bg-amber-400",
                "text_class": "text-amber-300",
            }
        return {
            "emoji": "🟢",
            "bar_class": "bg-emerald-500",
            "text_class": "text-emerald-400",
        }

    def _score_color_class(self, score: float) -> str:
        return self._status(score)["text_class"]

    def _escape(self, text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def _js_string(self, text: str) -> str:
        escaped = text.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"


DashboardBuilder = DashboardGenerator
