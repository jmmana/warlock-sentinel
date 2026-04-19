from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Literal
from uuid import uuid4

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
  <title>Warlock Sentinel • Quality Report</title>
  <script src=\"https://cdn.tailwindcss.com\"></script>
</head>
<body class=\"bg-slate-950 text-slate-100 min-h-screen\">
  <div class=\"max-w-7xl mx-auto px-4 md:px-8 py-8\">
    <header class=\"relative overflow-hidden mb-8 p-6 md:p-8 rounded-3xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950 shadow-2xl shadow-indigo-950/40\">
      <div class=\"absolute -top-16 -right-16 w-56 h-56 bg-cyan-500/10 rounded-full blur-3xl\"></div>
      <div class=\"absolute -bottom-20 -left-12 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl\"></div>

      <div class=\"relative grid grid-cols-1 lg:grid-cols-3 gap-6 items-center\">
        <div class=\"lg:col-span-1\">
          <p class=\"text-cyan-300 uppercase tracking-[0.2em] text-xs font-semibold\">Warlock Sentinel</p>
          <h1 class=\"text-3xl md:text-4xl font-black mt-2 leading-tight\">Warlock Sentinel • Quality Report</h1>
          <p class=\"text-slate-300 mt-4\">Proyecto: <span class=\"font-semibold\">{self._escape(project_name)}</span></p>
        </div>

        <div class=\"lg:col-span-1 flex justify-center\">
          <div class=\"relative w-44 h-44 rounded-full border-8 {self._ring_color_class(health_score)} bg-slate-950/70 grid place-items-center shadow-2xl\">
            <div class=\"absolute inset-3 rounded-full border border-slate-700/80\"></div>
            <div class=\"relative text-center\">
              <p class=\"text-xs text-slate-400 uppercase tracking-wide\">Global Health</p>
              <p class=\"text-5xl font-black {self._score_color_class(health_score)}\">{health_score:.0f}</p>
              <p class=\"text-xs text-slate-400\">{health_score:.2f}%</p>
            </div>
          </div>
        </div>

        <div class=\"lg:col-span-1 space-y-3\">
          <button
            id=\"rerun-warlock\"
            class=\"w-full bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-400 hover:to-indigo-400 text-slate-950 font-black px-7 py-4 rounded-2xl shadow-xl shadow-indigo-900/50 transition-transform hover:-translate-y-0.5\"
          >
            Re-ejecutar Warlock ahora
          </button>
          <p id=\"copy-feedback\" class=\"text-xs text-slate-400\">Comando: <span class=\"font-mono\">{self._escape(rerun_command)}</span></p>

          <div class=\"grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2\">
            <div class=\"rounded-xl border border-slate-800 bg-slate-900/70 p-3\">
              <p class=\"text-xs text-slate-400\">Coverage Total</p>
              <p class=\"text-2xl font-black {self._score_color_class(report.total_coverage)}\">{report.total_coverage:.2f}%</p>
            </div>
            <div class=\"rounded-xl border border-slate-800 bg-slate-900/70 p-3\">
              <p class=\"text-xs text-slate-400\">Módulos Analizados</p>
              <p class=\"text-2xl font-black text-slate-100\">{len(modules)}</p>
            </div>
          </div>
          <p class=\"text-xs text-slate-400\">Fecha y hora: {self._escape(generated_at)}</p>
        </div>
      </div>
    </header>

    <main class=\"space-y-4\">
      <section class=\"mb-2\">
        <h2 class=\"text-2xl font-black\">Módulos del Proyecto</h2>
        <p class=\"text-slate-400 text-sm\">Explora cada módulo para revisar cobertura y estado por archivo.</p>
      </section>
      {module_cards or '<div class="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-slate-300">No hay datos de coverage disponibles.</div>'}
    </main>

    <footer class=\"mt-8 text-center text-xs text-slate-500\">Generado por Warlock Sentinel</footer>
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
    const feedback = document.getElementById('copy-feedback');
    if (rerunButton) {{
      rerunButton.addEventListener('click', async () => {{
        const cmd = {self._js_string(rerun_command)};
        try {{
          if (navigator.clipboard && navigator.clipboard.writeText) {{
            await navigator.clipboard.writeText(cmd);
            if (feedback) feedback.textContent = `Comando copiado al portapapeles: ${{cmd}}`;
          }} else {{
            if (feedback) feedback.textContent = `Ejecuta en terminal: ${{cmd}}`;
          }}
        }} catch (_error) {{
          if (feedback) feedback.textContent = `Ejecuta en terminal: ${{cmd}}`;
        }}
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
            )

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
        module_id = f"module-{uuid4().hex}"
        file_rows = "\n".join(self._render_file_row(file_cov) for file_cov in module.files)

        return f"""
<section class=\"rounded-2xl border border-slate-800 bg-slate-900/80 overflow-hidden shadow-lg shadow-black/20\">
  <button data-accordion-toggle=\"{module_id}\" class=\"w-full text-left p-5 hover:bg-slate-800/60 transition\">
    <div class=\"flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4\">
      <div>
        <p class=\"text-slate-300 text-sm\">Módulo</p>
        <h2 class=\"text-2xl font-black flex items-center gap-3\"><span class=\"text-2xl\">{status['emoji']}</span>{self._escape(module.name)}</h2>
      </div>
      <div class=\"flex flex-wrap items-center gap-3 text-sm\">
        <span class=\"px-3 py-1.5 rounded-lg border border-slate-700\">Archivos: {len(module.files)}</span>
        <span class=\"text-3xl font-black {status['text_class']}\">{module.coverage:.2f}%</span>
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
        height = "h-2.5" if compact else "h-5"
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

    def _ring_color_class(self, score: float) -> str:
        if score < 60:
            return "border-red-500"
        if score < 80:
            return "border-amber-400"
        return "border-emerald-500"

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
