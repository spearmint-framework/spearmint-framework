# Repository Guidelines

## Project Overview
Spearmint is a Python experiment framework for testing multiple configurations of code (A/B-style experiments). It provides decorators and runners to execute a primary config plus variants, optionally in the background.

## Architecture & Data Flow
- **Public API**: `Spearmint`, `experiment`, `Config` exported from `src/spearmint/__init__.py`.
- **Experiment registration**: `@Spearmint.experiment()` or module-level `@experiment()` wraps a function into an `ExperimentFunction` and registers it in the global registry (`src/spearmint/registry.py`).
- **Configuration parsing**: `parse_configs()` accepts dicts, Pydantic models, or YAML paths and returns `Config` instances; `DynamicValue` expands parameter sweeps into cartesian products (`src/spearmint/configuration/__init__.py`, `dynamic_value.py`, `config.py`).
- **Execution**:
  - `Spearmint.run()` / `Spearmint.arun()` create an `ExperimentRunner` (`src/spearmint/runner.py`).
  - `ExperimentFunction.get_experiment_cases()` computes main + variant cases (including nested experiments) using a cartesian product of configs.
  - `ExperimentRunner` executes the main case and optional variants (sync via threads or async tasks), returning `ExperimentCaseResults`.
- **State propagation**: Uses `contextvars` for current experiment case and runner (`src/spearmint/context.py`) so nested experiments share the same execution context.

## Key Directories
- `src/spearmint/` — core library (configuration, runner, registry, context).
- `src/tests/` — pytest-based test suite.
- `cookbook/` — runnable examples (used in tests).
- `docs/` — documentation site (Diátaxis structure).
- `.github/workflows/` — CI for docs deploy and PyPI release.

## Development Commands
Use `uv` to manage deps and run commands (per `.github/copilot_instructions.md`).

Common commands (prefix with `uv run`):
- Tests: `pytest src/tests` (uses `pytest-asyncio`, `pytest-cov`).
- Lint: `ruff` (configured in `pyproject.toml`).
- Type check: `mypy` (strict mode in `pyproject.toml`).
- Docs:
  - Serve: `mkdocs serve` (per `docs/CONTRIBUTING.md`).
  - Build: `mkdocs build` (per `docs/CONTRIBUTING.md`).
- Build package (CI): `python -m build --wheel --sdist` (per `.github/workflows/python-publish.yml`).

## Code Conventions & Common Patterns
- **Typing**: Strong typing with `mypy` strict; prefer explicit annotations. Annotate async functions and return types.
- **Config injection**:
  - Use `Config` or Pydantic models as function parameters to receive injected config.
  - Use `Annotated[Model, Bind("path")]` to bind nested config paths (`src/spearmint/experiment_function.py`).
- **Decorator usage**:
  - `@mint.experiment()` (instance method) or `@experiment(configs=[...])` (module-level helper).
- **Async patterns**:
  - `Spearmint.arun()` for async execution; sync runner can execute async functions via `_run_coroutine_sync`.
- **Error handling**:
  - Missing experiment context raises `RuntimeError` (runner).
  - Missing config bindings raise `ValueError` (binding logic).
  - YAML path validation raises `FileNotFoundError` (handlers).
- **Formatting**: Ruff target version `py310`, line length `100` (see `pyproject.toml`).

## Important Files
- `src/spearmint/__init__.py` — public exports.
- `src/spearmint/spearmint.py` — main API class and module-level decorator.
- `src/spearmint/runner.py` — execution engine and result types.
- `src/spearmint/experiment_function.py` — config binding and injection logic.
- `src/spearmint/configuration/` — `Config`, `DynamicValue`, config parsing/generation.
- `src/spearmint/context.py` — contextvars for runtime state.
- `src/tests/test_spearmint.py` — primary test suite.
- `pyproject.toml` — dependencies, tooling config, build system.
- `uv.lock` — dependency lock file.
- `mkdocs.yml` — docs site config.

## Runtime/Tooling Preferences
- **Runtime**: Python `>=3.10` (see `pyproject.toml`).
- **Package manager**: `uv` (see `.github/copilot_instructions.md`, `uv.lock`).
- **Build system**: `hatchling` (see `pyproject.toml`).

## Testing & QA
- **Frameworks**: `pytest`, `pytest-asyncio`, `pytest-cov` (see `pyproject.toml`).
- **Test locations**: `src/tests/test_spearmint.py` (includes cookbook sample execution via `runpy`).
- **Coverage**: Configured in `pyproject.toml` (`[tool.coverage.*]`).
- **Expectations**: Run tests via `uv run pytest src/tests`; keep type checking (`uv run mypy`) and lint (`uv run ruff`) clean.