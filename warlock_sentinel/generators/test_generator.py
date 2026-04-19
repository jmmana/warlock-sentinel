from __future__ import annotations

import asyncio
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from rich.console import Console

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - runtime dependency availability differs by environment
    genai = None

from warlock_sentinel.coverage.parser import CoverageGap
from warlock_sentinel.project_detector import ProjectInfo


FRAMEWORK_TEMPLATE_MAP: dict[str, str] = {
    "flutter": "flutter_test.jinja2",
    "react": "react_test.jinja2",
    "angular": "angular_test.jinja2",
    "csharp": "csharp_test.jinja2",
    "nextjs": "nextjs_test.jinja2",
    "vue": "vue_test.jinja2",
    "nestjs": "nestjs_test.jinja2",
}

STACK_TEMPLATE_MAP: dict[str, str] = {
    "nextjs": "nextjs_test.jinja2",
    "vue": "vue_test.jinja2",
    "nestjs": "nestjs_test.jinja2",
}


class TestGenerator:
    def __init__(
        self,
        gemini_api_key: str | None,
        model: str = "gemini-2.0-flash-thinking-exp-01-21",
    ) -> None:
        self.gemini_api_key = gemini_api_key
        self.model = model
        self.console = Console()
        templates_dir = Path(__file__).resolve().parents[1] / "templates"
        self.template_env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=False)

    async def generate_tests(
        self,
        project_info: ProjectInfo,
        file_path: str,
        coverage_gaps: list[CoverageGap],
    ) -> str:
        """Generate test code for a source file and its precise coverage gaps."""
        source_code = await asyncio.to_thread(self._read_source_file, file_path)
        prompt = self._build_prompt(
            project_info=project_info,
            file_path=file_path,
            source_code=source_code,
            coverage_gaps=coverage_gaps,
        )

        if self.gemini_api_key and genai is not None:
            with self.console.status("[cyan]Generating tests with Gemini...[/cyan]"):
                model_output = await asyncio.to_thread(self._call_gemini, prompt)
            if model_output.strip():
                return self._extract_code_block(model_output)

        self.console.print("[yellow]Gemini unavailable, returning deterministic template fallback.[/yellow]")
        return self._render_fallback_template(project_info=project_info, file_path=file_path)

    async def fix_test(
        self,
        project_info: ProjectInfo,
        file_path: str,
        source_code: str,
        failed_test_code: str,
        console_error: str,
    ) -> str:
        """Repair a failing generated test using only the failing test and the console error."""
        prompt = self._build_fix_prompt(
            project_info=project_info,
            file_path=file_path,
            source_code=source_code,
            failed_test_code=failed_test_code,
            console_error=console_error,
        )

        if self.gemini_api_key and genai is not None:
            with self.console.status("[cyan]Repairing test with Gemini...[/cyan]"):
                model_output = await asyncio.to_thread(self._call_gemini, prompt)
            if model_output.strip():
                return self._extract_code_block(model_output)

        self.console.print("[yellow]Repair model unavailable, keeping existing test code.[/yellow]")
        return failed_test_code

    def _build_prompt(
        self,
        project_info: ProjectInfo,
        file_path: str,
        source_code: str,
        coverage_gaps: list[CoverageGap],
    ) -> str:
        template_name = self._resolve_template_name(project_info)
        prompt_template = self.template_env.get_template(template_name)

        return prompt_template.render(
            framework=project_info.framework,
            target_coverage=85,
            file_name=Path(file_path).name,
            state_management=self._detect_state_management(project_info),
            backend_tech=self._detect_backend_tech(project_info),
            test_tool=self._test_tool(project_info),
            mock_library=self._mock_library(project_info),
            language=project_info.language,
            stacks=", ".join(project_info.stacks) if project_info.stacks else "none",
            metadata=project_info.metadata,
            file_path=file_path,
            source_code=source_code,
            coverage_gaps=coverage_gaps,
            knowledge_base=self._knowledge_base(project_info),
        )

    def _resolve_template_name(self, project_info: ProjectInfo) -> str:
        for stack in project_info.stacks:
            if stack in STACK_TEMPLATE_MAP:
                return STACK_TEMPLATE_MAP[stack]
        return FRAMEWORK_TEMPLATE_MAP.get(project_info.framework, "react_test.jinja2")

    def _build_fix_prompt(
        self,
        project_info: ProjectInfo,
        file_path: str,
        source_code: str,
        failed_test_code: str,
        console_error: str,
    ) -> str:
        prompt_template = self.template_env.get_template("fix_test.jinja2")
        return prompt_template.render(
            framework=project_info.framework,
            file_name=Path(file_path).name,
            state_management=self._detect_state_management(project_info),
            backend_tech=self._detect_backend_tech(project_info),
            test_tool=self._test_tool(project_info),
            mock_library=self._mock_library(project_info),
            source_code=source_code,
            failed_test_code=failed_test_code,
            console_error=console_error,
            knowledge_base=self._knowledge_base(project_info),
        )

    def _call_gemini(self, prompt: str) -> str:
        if not self.gemini_api_key:
            return ""
        if genai is None:
            return ""

        genai.configure(api_key=self.gemini_api_key)
        model = genai.GenerativeModel(self.model)
        response = model.generate_content(prompt)

        text = getattr(response, "text", None)
        if isinstance(text, str):
            return text

        return ""

    def _render_fallback_template(self, project_info: ProjectInfo, file_path: str) -> str:
        if project_info.framework == "flutter":
            return (
                "import 'package:flutter_test/flutter_test.dart';\n"
                "import 'package:mocktail/mocktail.dart';\n\n"
                f"void main() {{\n  group('Generated fallback for {Path(file_path).name}', () {{\n"
                "    test('should validate behavior', () {\n"
                "      expect(true, isTrue);\n"
                "    });\n"
                "  });\n}\n"
            )

        if project_info.framework == "angular":
            return (
                "import { TestBed } from '@angular/core/testing';\n"
                "import { of } from 'rxjs';\n\n"
                f"describe('Generated fallback for {Path(file_path).name}', () => {{\n"
                "  it('validates expected behavior', () => {\n"
                "    expect(true).toBeTrue();\n"
                "  });\n"
                "});\n"
            )

        if project_info.framework == "csharp":
            return (
                "using Xunit;\n\n"
                f"public class GeneratedFallback_{Path(file_path).stem} {{\n"
                "    [Fact]\n"
                "    public void ValidatesExpectedBehavior() {\n"
                "        Assert.True(true);\n"
                "    }\n"
                "}\n"
            )

        return (
            "import { describe, it, expect } from '@jest/globals';\n\n"
            f"describe('Generated fallback for {Path(file_path).name}', () => {{\n"
            "  it('validates expected behavior', () => {\n"
            "    expect(true).toBe(true);\n"
            "  });\n"
            "});\n"
        )

    def _detect_state_management(self, project_info: ProjectInfo) -> str:
        if project_info.framework == "flutter" and "riverpod" in project_info.stacks:
            return "Riverpod"
        if "pinia" in project_info.stacks:
            return "Pinia"
        if project_info.framework == "react" and "redux" in project_info.stacks:
            return "Redux"
        if project_info.framework == "react" and "zustand" in project_info.stacks:
            return "Zustand"
        if project_info.framework == "angular" and "ngrx" in project_info.stacks:
            return "NgRx"
        if "nestjs" in project_info.stacks:
            return "NestJS DI"
        if project_info.framework == "csharp":
            return "Dependency Injection"
        return "Unknown/Standard"

    def _detect_backend_tech(self, project_info: ProjectInfo) -> str:
        if "supabase" in project_info.stacks:
            return "Supabase"
        return "HTTP/API layer"

    def _test_tool(self, project_info: ProjectInfo) -> str:
        if project_info.framework == "flutter":
            return "flutter_test"
        if project_info.framework == "angular":
            return "Jasmine/Karma or Jest"
        if project_info.framework == "csharp":
            return "dotnet test + xUnit/NUnit"
        if "nestjs" in project_info.stacks:
            return "Jest + Nest TestingModule"
        if "vue" in project_info.stacks:
            return "Vitest/Jest + Vue Test Utils"
        return "Jest + RTL"

    def _mock_library(self, project_info: ProjectInfo) -> str:
        if project_info.framework == "flutter":
            return "mocktail / riverpod_test"
        if project_info.framework == "angular":
            return "Jest spies / TestBed / Jasmine mocks"
        if project_info.framework == "csharp":
            return "Moq / FakeItEasy"
        if "nestjs" in project_info.stacks:
            return "Jest mocks / provider overrides"
        if "vue" in project_info.stacks:
            return "Vue Test Utils stubs / module mocks"
        return "MSW / jest mocks"

    def _knowledge_base(self, project_info: ProjectInfo) -> str:
        if "supabase" not in project_info.stacks:
            return ""

        rules: list[str] = ["Supabase mocking rules:"]
        if project_info.framework == "flutter":
            rules.append("- Use mocktail to intercept client.from('table').select().")
            rules.append("- Prefer typed fakes over real network calls.")
        elif project_info.framework == "angular":
            rules.append("- Mock the Supabase service with of(mockData) to preserve RxJS reactivity.")
            rules.append("- Keep observables cold and deterministic in tests.")
        elif project_info.framework == "csharp":
            rules.append("- Use interfaces for Supabase.Client and inject them via dependency inversion.")
            rules.append("- Generate test data as JSON fixtures or strongly typed DTOs.")
        else:
            rules.append("- Mock the Supabase boundary rather than the business logic.")

        return "\n".join(rules)

    def _read_source_file(self, file_path: str) -> str:
        return Path(file_path).read_text(encoding="utf-8")

    def _extract_code_block(self, raw_output: str) -> str:
        output = raw_output.strip()
        if not output.startswith("```"):
            return output

        lines = output.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
