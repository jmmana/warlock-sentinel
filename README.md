# 🔮 Warlock Sentinel

<div align="center">

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub](https://img.shields.io/badge/github-jmmana%2Fwarlock--sentinel-black?logo=github)](https://github.com/jmmana/warlock-sentinel)
[![Gemini AI](https://img.shields.io/badge/AI-Gemini-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)

**The AI-Powered Test Generation Engine for Modern Frontend Projects**

_Automate your test coverage, heal your gaps, and maintain quality with zero friction._

</div>

---

## ⚡ What is Warlock Sentinel?

Warlock Sentinel is an **intelligent testing automation platform** that transforms fragmented test suites into production-grade quality gates. It combines **framework detection**, **coverage analysis**, **AI-driven test generation**, and **self-healing loops** to keep your codebase tested and healthy.

### The Complete Cycle

```
🔍 Detect  →  📊 Analyze  →  🤖 Generate  →  ✅ Execute  →  📈 Report
```

1. **🔍 Smart Detection** - Auto-detects your framework and project structure
2. **📊 Coverage Analysis** - Identifies testing gaps at line-level precision  
3. **🤖 AI Generation** - Leverages Gemini to write semantically correct tests
4. **✅ Execution & Validation** - Runs tests immediately, catches failures
5. **📈 Self-Healing** - Repairs failing tests automatically (up to 3 attempts)
6. **📊 Dashboard** - Visual health score and coverage trends

---

## 🎯 Supported Frameworks

| Framework | Language | Support | Icon |
|-----------|----------|---------|------|
| **Flutter** | Dart | ✅ Full SDET | 🦋 |
| **React** | TypeScript/JSX | ✅ Full SDET | ⚛️ |
| **Next.js** | TypeScript | ✅ Full SDET | ▲ |
| **Vue** | TypeScript | ✅ Full SDET | 💚 |
| **Angular** | TypeScript | ✅ Full SDET | 🅰️ |
| **NestJS** | TypeScript | ✅ Full SDET | 🪺 |
| **C#** | C# | ✅ Full SDET | #️⃣ |

**And growing!** The adapter-based architecture makes adding new frameworks frictionless.

---

## 🚀 Quick Start

### Install

```bash
pipx install warlock-sentinel
```

### Initialize

```bash
cd /path/to/your-project
warlock init
export GEMINI_API_KEY="your_api_key"
```

### Run

```bash
warlock
```

**That's it.** Dashboard appears at `.warlock/dashboard.html` when complete.

## 📋 Requirements

| Requirement | Why | Version |
|-------------|-----|---------|
| **Python** | Core runtime | 3.11+ |
| **Gemini API Key** | AI backbone | Free tier available |
| **Framework SDK** | Project execution | Framework-specific |

### By Framework

- **🦋 Flutter**: Flutter SDK installed, `pubspec.yaml` present
- **⚛️ React/Next.js/Vue/Angular**: Node.js 18+, `package.json` present
- **🪺 NestJS**: Node.js 18+, `package.json` with `@nestjs/core`
- **#️⃣ C#**: .NET 6+, `*.csproj` or `*.sln` present

## 📦 Installation

### Recommended: pipx (Isolated Environment)

```bash
pipx install warlock-sentinel
warlock --help  # Verify installation
```

### Alternative: pip (User-only)

```bash
python -m pip install --user warlock-sentinel
warlock --help
```

### Development: From Source

```bash
git clone https://github.com/jmmana/warlock-sentinel.git
cd warlock-sentinel
python -m pip install -e .
warlock --help
```

## 🎮 Usage

### Step 1: Enter Your Project

```bash
cd /path/to/your-project
```

### Step 2: Initialize Configuration

```bash
warlock init
```

Creates `sentinel.yaml` in your project root with sensible defaults.

### Step 3: Set API Key (Environment Variable)

```bash
export GEMINI_API_KEY="your_gemini_api_key"
```

> 💡 Get a free API key at [ai.google.dev](https://ai.google.dev/)

### Step 4: Run the Full Cycle

```bash
warlock
```

Warlock Sentinel will:
1. ✅ Detect your framework
2. ✅ Analyze coverage gaps  
3. ✅ Generate missing tests via AI
4. ✅ Execute tests and validate
5. ✅ Auto-heal failures
6. ✅ Generate a visual dashboard

**Output**: Check `.warlock/dashboard.html` in your browser.

## ⚙️ Configuration

Warlock Sentinel uses `sentinel.yaml` for project-level configuration.

### Example: sentinel.yaml

```yaml
# Project metadata
project_name: my-awesome-app
framework: auto  # Options: flutter, react, angular, csharp, vue, nestjs, or auto

# AI Engine Configuration
llm:
  provider: gemini
  model: gemini-2.5-pro  # Recommended for best quality
  api_key_env: GEMINI_API_KEY  # Read from environment
  temperature: 0.2  # Lower = more deterministic

# Coverage Goals
coverage:
  target: 85  # Aim for 85% coverage
  include:
    - lib/**
    - src/**
  exclude:
    - "**/*.g.dart"       # Generated files
    - "**/*.gen.ts"       # Generated files
    - "**/node_modules/**"
    - "**/__pycache__/**"

# Test Generation
generation:
  max_files_per_run: 20  # Limit per-run for cost control
  write_mode: overwrite  # Options: overwrite, merge, validate_only
  test_style: pragmatic  # Focus on real-world assertions

# Output & Reporting
output:
  dashboard_path: .warlock/dashboard.html
  report_json_path: .warlock/report.json
```

## 🛠️ Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `warlock init` | Create `sentinel.yaml` in current project | `warlock init` |
| `warlock` | Run full cycle (detect→analyze→generate→execute) | `warlock` |
| `warlock --help` | Show all available commands | `warlock --help` |
| `warlock <cmd> --help` | Show help for specific command | `warlock init --help` |

---

## 🔄 How It Works: The Self-Healing Cycle

Warlock Sentinel automates the entire testing lifecycle:

```
┌─────────────────────────────────────────────────────────────┐
│                  WARLOCK SENTINEL PIPELINE                  │
└─────────────────────────────────────────────────────────────┘

1️⃣  DETECTION
    ├─ Identifies framework (Flutter, React, Vue, etc.)
    ├─ Parses project structure and dependencies
    ├─ Detects state management (Redux, Riverpod, etc.)
    └─ Sets up test runner context

2️⃣  COVERAGE ANALYSIS
    ├─ Parses existing coverage reports (LCOV, Istanbul)
    ├─ Identifies untested lines and branches
    ├─ Maps gaps by file and function
    └─ Prioritizes critical paths

3️⃣  AI-POWERED GENERATION
    ├─ Routes to framework-specific prompt template
    ├─ Feeds source code + gaps to Gemini
    ├─ Applies SDET discipline (deterministic, focused)
    └─ Generates syntactically valid tests

4️⃣  EXECUTION & VALIDATION
    ├─ Runs newly generated tests immediately
    ├─ Captures failures and console errors
    └─ Validates coverage improvement

5️⃣  AUTO-HEALING
    ├─ If tests fail, repair with Gemini (up to 3 attempts)
    ├─ Feeds error context and source back to AI
    ├─ Validates each repair iteration
    └─ Tracks refactor candidates for future review

6️⃣  REPORTING
    ├─ Aggregates results into JSON report
    ├─ Generates interactive HTML dashboard
    ├─ Shows health score, trends, and insights
    └─ Exports actionable recommendations
```

**Key Feature: SDET Discipline** 🎓  
All generated tests follow Software Development Engineer in Test (SDET) best practices:
- ✅ Deterministic assertions (no flaky waits)
- ✅ Proper mocking (Supabase, Riverpod, Mocktail)
- ✅ Framework-specific semantics (TestBed for Angular, widget testing for Flutter)
- ✅ Error path coverage (exceptions, edge cases)

---

## 📊 Supported Features by Framework

| Feature | Flutter | React | Angular | C# | Vue | NestJS | Next.js |
|---------|---------|-------|---------|-----|-----|--------|---------|
| Auto-Detection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Coverage Parsing | ✅ LCOV | ✅ Istanbul | ✅ LCOV | ✅ | ✅ LCOV | ✅ LCOV | ✅ Istanbul |
| Test Generation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Self-Healing | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 📁 Architecture at a Glance

```
warlock_sentinel/
├── cli.py                 # Command-line interface (Typer)
├── config.py              # YAML configuration loader
├── project_detector.py    # Framework & stack detection
├── adapters/              # Framework-specific implementations
│   ├── flutter_adapter.py
│   ├── react_adapter.py
│   └── ...
├── generators/
│   └── test_generator.py  # AI-powered test generation engine
├── coverage/
│   └── report.py          # Coverage parsing (LCOV, Istanbul)
├── dashboard/
│   └── builder.py         # HTML report generation
└── templates/             # Jinja2 prompt templates (by framework)
    ├── base_prompt.jinja2
    ├── flutter_test.jinja2
    ├── react_test.jinja2
    └── ...
```

**Design Principles:**
- 🔌 **Pluggable**: Adapter pattern for framework extensibility
- 🎯 **Focused**: Single responsibility per module
- 🧪 **Testable**: Decoupled core logic from CLI
- 📦 **Portable**: Ship templates with package, no external deps

---

## 💡 Quick Tips

### For Best Results:

1. **Start with a high-coverage project** - Easier to improve than starting from scratch
2. **Review AI-generated tests** - Always validate before committing
3. **Set realistic coverage targets** - 85% is usually sufficient
4. **Run in CI** - Integrate with GitHub Actions, GitLab CI, etc.
5. **Monitor trends** - Use the dashboard to track progress over time

### Environment Setup:

```bash
# Get your free Gemini API key
export GEMINI_API_KEY="your_key_here"

# Optional: Customize test output directory
export WARLOCK_OUTPUT_DIR=".warlock"

# Optional: Enable debug logging
export WARLOCK_DEBUG=1
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `warlock: command not found` | Reinstall: `pipx install --force-reinstall warlock-sentinel` |
| Framework not detected | Run in project root, ensure `package.json` or `pubspec.yaml` exists |
| Gemini API errors | Check API key, verify quota at [console.cloud.google.com](https://console.cloud.google.com) |
| Tests fail to execute | Ensure test runner is installed (`flutter test`, `npm test`, `npm run test:unit`) |
| Low coverage improvement | Check `coverage.exclude` patterns in `sentinel.yaml` |

---

## 🤝 Contributing

We welcome contributions! Areas of interest:
- New framework adapters (Svelte, Qwik, etc.)
- Enhanced prompt templates for existing frameworks
- Coverage parser improvements
- Dashboard UI enhancements

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🚀 Get Started Now

```bash
# 1. Install
pipx install warlock-sentinel

# 2. Initialize
cd /path/to/your-project
warlock init

# 3. Configure
export GEMINI_API_KEY="your_key"

# 4. Run
warlock

# 5. View results
open .warlock/dashboard.html
```

**Questions?** Open an issue at [github.com/jmmana/warlock-sentinel](https://github.com/jmmana/warlock-sentinel)

---

<div align="center">

**Made with 🔮 by [jmmana](https://github.com/jmmana)**

</div>

## Roadmap

- Vue/Nuxt adapters
- Angular adapter
- Modo incremental para PRs
- Reintentos automáticos de generación basados en fallos de tests

## Licencia

MIT
