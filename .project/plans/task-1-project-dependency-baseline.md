# Detailed Task 1: Project & Dependency Baseline

Goal: Establish a clean, reproducible development environment with required runtime + dev dependencies, quality gates, and initial folder scaffolding (without premature modules). All changes should be testable via installing the project in editable mode.

## Subtasks
1. Inspect existing `pyproject.toml`.
2. Add core runtime dependencies:
   - `pydantic` (>=2, pin minor version) for future config expansion.
   - `mlflow` as optional extra (`[project.optional-dependencies]` or Poetry extras) named `mlflow`.
3. Add dev dependencies:
   - `pytest`, `pytest-asyncio` for async test support.
   - `mypy` for static typing.
   - `ruff` (or `flake8`) for linting; choose `ruff` (faster, modern) with a minimal config.
   - `coverage` via `pytest-cov`.
4. Configure tool sections / ruff / mypy in `pyproject.toml`.
5. Ensure `src/spearmint/py.typed` exists (already present) to mark typed package.
6. Add initial empty module stubs (only if missing) to match spec future paths without implementation: `branch.py`, `strategies.py`, `logging.py`, `config.py`, `experiment.py`, `registry.py` containing docstring placeholders and TODO markers. Keep them minimal—no logic yet.
7. Create `tests/conftest.py` with shared fixtures (e.g., event loop fixture if needed, in-memory logger fixture stub placeholder).
8. Avoid Makefile unless essential (YAGNI). Provide README section with commands instead.
9. Update `README.md` quickstart section: installation, optional MLflow extra, running tests.
10. Verify installation workflow:
    - `python -m pip install -e .[mlflow]`
    - `pytest -q` (should pass with placeholder tests).

## File-Level Guidance
- `pyproject.toml`: Add dependencies, `[tool.mypy]`, `[tool.ruff]`, and optional extras section.
- `src/spearmint/__init__.py`: Export key public symbols progressively (initially version constant + placeholder). Avoid re-exporting unfinished modules.
- New stub files: Add module-level docstring: purpose + acceptance criteria reference + TODO list.
- `tests/test_imports.py`: Simple smoke test ensuring modules import without error.

## Testing Strategy (TDD)
Write failing smoke tests first (import modules that will be created). Then create stub files to satisfy them.

Test Cases:
1. Import `spearmint` root succeeds.
2. Import each stub module (`from spearmint import branch, strategies, logging, config, experiment, registry`).
3. Access `__version__` attribute from `spearmint`.

Edge Cases:
- Missing optional MLflow: Ensure importing `logging` does not raise if MLflow absent (guarded import placeholder).
- Python versions: Ensure classifiers and requires-python reflect target (e.g., `>=3.9`).

## Acceptance Criteria
- Editable install works.
- Optional MLflow extra declared.
- Lint and type configs present.
- Smoke tests green.
- No unused placeholder logic beyond docstrings.

## Commit Granularity
1. Add deps + tool configs.
2. Add stub modules + py.typed confirmation.
3. Add smoke tests + fixtures.
4. README quickstart update.
