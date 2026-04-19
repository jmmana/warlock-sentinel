# Warlock Sentinel

Warlock Sentinel es un AI Testing Agent para proyectos frontend que automatiza el ciclo de calidad:

1. Detecta framework y estado actual del proyecto.
2. Analiza cobertura y gaps de testing.
3. Genera tests faltantes con IA.
4. Ejecuta tests y coverage.
5. Genera un dashboard con resultados y health score.

El objetivo es que lo puedas instalar una vez y ejecutarlo en cualquier repositorio Flutter o React/Next.js.

## Soporte Inicial de Frameworks

- Flutter (Dart)
- React / Next.js (TypeScript)

La arquitectura basada en adapters permite agregar más frameworks sin romper el flujo principal.

## Requisitos

- Python 3.11+
- Acceso a Google Generative AI (Gemini)
- Dependencias del framework del proyecto objetivo:
	- Flutter SDK para proyectos Flutter
	- Node.js + package manager para proyectos React/Next.js

## Instalación Global

### Opción recomendada: pipx

```bash
pipx install warlock-sentinel
```

### Opción alternativa: pip usuario

```bash
python -m pip install --user warlock-sentinel
```

Verifica la instalación:

```bash
warlock --help
```

## Uso en Cualquier Proyecto

Warlock Sentinel se ejecuta dentro del repositorio que quieres auditar/mejorar.

### 1. Entra al proyecto objetivo

```bash
cd /ruta/a/tu-proyecto
```

### 2. Inicializa la configuración

```bash
warlock init
```

Esto crea un archivo `sentinel.yaml` en la raíz del proyecto actual.

### 3. Configura API key y ajustes

Define tu credencial de Gemini en tu entorno (recomendado):

```bash
export GEMINI_API_KEY="tu_api_key"
```

También puedes declarar la clave en el archivo de configuración si tu política interna lo permite.

### 4. Ejecuta el ciclo completo

```bash
warlock
```

Warlock Sentinel hará detección, análisis, generación de tests, ejecución y reporte.

## Ejemplo de sentinel.yaml

```yaml
project_name: my-frontend-app
framework: auto

llm:
	provider: gemini
	model: gemini-2.5-pro
	api_key_env: GEMINI_API_KEY
	temperature: 0.2

coverage:
	target: 85
	include:
		- lib/**
		- src/**
	exclude:
		- **/*.g.dart
		- **/*.gen.ts
		- **/node_modules/**

generation:
	max_files_per_run: 20
	write_mode: overwrite
	test_style: pragmatic

output:
	dashboard_path: .warlock/dashboard.html
	report_json_path: .warlock/report.json
```

## Comandos Disponibles

### warlock init

Inicializa configuración en el proyecto actual.

```bash
warlock init
```

### warlock

Ejecuta el ciclo de autocuración completo.

```bash
warlock
```

### warlock --help

Muestra ayuda general y comandos.

```bash
warlock --help
```

### warlock <comando> --help

Muestra ayuda específica del subcomando.

```bash
warlock init --help
```

## Ciclo de Autocuración

Warlock Sentinel implementa este pipeline:

1. Análisis
	 - Detecta si el repositorio es Flutter o React/Next.
	 - Evalúa estructura y archivos relevantes.
	 - Identifica áreas con cobertura insuficiente.
2. Generación de tests
	 - Usa prompts y templates Jinja2 por framework.
	 - Genera tests orientados a maximizar cobertura útil.
3. Ejecución
	 - Corre test runner y coverage del framework detectado.
	 - Captura resultados y métricas.
4. Dashboard
	 - Construye un reporte legible con estado, cobertura y health score.
	 - Facilita decisiones de refactor y priorización.

## Estructura Esperada del Proyecto de Warlock Sentinel

```text
warlock-sentinel/
├── warlock_sentinel/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── project_detector.py
│   ├── adapters/
│   ├── core/
│   ├── generators/
│   ├── coverage/
│   ├── dashboard/
│   └── templates/
├── tests/
├── .gitignore
├── pyproject.toml
├── README.md
├── LICENSE
└── sentinel.yaml.example
```

## Diseño Técnico (Resumen)

- CLI con Typer + Rich para DX limpia y mensajes claros.
- Adapters por framework para extensión futura.
- Núcleo de ejecución desacoplado para facilitar testing.
- Templates en paquete para versionado consistente.
- Configuración por YAML para adopción rápida en cualquier repo.

## Buenas Prácticas de Uso

- Ejecuta Warlock Sentinel en ramas de feature.
- Revisa y valida tests generados antes de merge.
- Configura `coverage.target` por tipo de proyecto.
- Integra `warlock` en CI para evitar regresiones.

## Troubleshooting Rápido

- `warlock: command not found`
	- Verifica que el binario esté en tu `PATH`.
	- Reinstala con `pipx install warlock-sentinel`.
- No detecta framework
	- Asegura que el comando se ejecute en la raíz del proyecto objetivo.
	- Verifica que existan archivos base (`pubspec.yaml` o `package.json`).
- Error de API Gemini
	- Revisa `GEMINI_API_KEY`.
	- Verifica cuotas/permisos del proveedor.

## Roadmap

- Vue/Nuxt adapters
- Angular adapter
- Modo incremental para PRs
- Reintentos automáticos de generación basados en fallos de tests

## Licencia

MIT
