# Spearmint MVP Implementation Task Plan

Guiding principles: DRY, YAGNI, TDD-first (write/extend tests before production code), frequent small commits (each task or subtask), clear separation of concerns, minimal surface area for MVP.

## High-Level Task Outline

1. Project & Dependency Baseline
   - Confirm `pyproject.toml` structure, add optional MLflow dependency (extras) and Pydantic.
   - Add dev tooling: pytest, mypy, ruff (or flake8), coverage config.

2. Core Types & Data Models
   - Implement `Branch` dataclass and related `BranchContainer` abstraction.
   - Define common enums / constants (status strings) and type aliases in `types.py`.

3. Logging Layer
   - Define `LoggerBackend` protocol.
   - Implement MLflow backend (guarded import, graceful no-MLflow fallback).
   - Add minimal test double (InMemoryLogger) for unit tests.

4. Strategy Protocol & Built-in Strategies
   - Define `Strategy` protocol interface.
   - Implement `RoundRobinStrategy`, `ShadowStrategy`, `MultiBranchStrategy` with concurrency semantics.
   - Ensure consistent branch creation & logging per strategy.

5. Strategy Registry
   - Implement registration API (register, get, list) with simple internal mapping.
   - Support user-provided custom strategy classes.

6. Configuration Management Utilities
   - YAML loader (directory + file paths) -> list of dict configs.
   - Pydantic expansion utility (model-driven variant generation).
   - Config ID canonicalization (hash stub + TODO for future refinement).

7. Experiment Decorator
   - Implement `@experiment` decorator wrapping async functions.
   - Delegate execution to chosen strategy; manage config pool injection.
   - Provide inspection hooks (e.g., access to last branches for single-result strategies).

8. Error Handling & Metadata Capture
   - Implement per-branch exception capture & structuring.
   - Ensure logging of exceptions and statuses (success/failed/skipped).

9. Testing Suite
   - Unit tests for: Branch model, LoggerBackend (in-memory), each Strategy behavior, decorator orchestration, config loader & expansion.
   - Concurrency tests (ensuring background vs awaited tasks semantics).
   - Type checking & linting integrated in CI (placeholder local script).

10. Example Usage & Documentation
    - `examples/` updated: illustrate all strategies.
    - README Quickstart + design summary + limitation notes.

11. Optional: Sync Function Support Wrapper
    - Provide internal wrapper to run sync functions in thread executor (minimal feature per acceptance criteria).

12. Polishing & Validation
    - Mypy type coverage pass.
    - Ruff/flake8 lint cleanup.
    - Coverage target (~85%+) for core modules.
    - Final review against acceptance criteria.

13. Future-Proofing Stubs (Non-invasive)
    - Place TODO markers for retries, streaming container, cancellation.
    - Minimal hook points (internal protected methods) without implementing full hook system.

## Task Execution Order (Suggested)
Order optimized to enable TDD layering and early feedback loops.

1. Project & Dependency Baseline
2. Core Types & Data Models
3. Logging Layer (+ in-memory test backend)
4. Strategy Protocol & Built-ins
5. Strategy Registry
6. Configuration Management Utilities
7. Experiment Decorator
8. Error Handling & Metadata Capture (integrated while refining strategies/decorator)
9. Testing Suite (iteratively built alongside tasks 2–8)
10. Example Usage & Documentation
11. Sync Function Support Wrapper
12. Polishing & Validation
13. Future-Proofing Stubs

## Next Steps
Await confirmation of this high-level outline before expanding each task into detailed, step-by-step instructions with file-level guidance and test plans.

---

## Detailed Task 1: Project & Dependency Baseline

Goal: Establish a clean, reproducible development environment with required runtime + dev dependencies, quality gates, and initial folder scaffolding (without premature modules). All changes should be testable via installing the project in editable mode.

### Subtasks
1. Inspect existing `pyproject.toml`.
2. Add core runtime dependencies:
   - `pydantic` (>=2, pin minor version) for config expansion.
   - `mlflow` as optional extra (`[project.optional-dependencies]` or Poetry extras) named `mlflow`.
3. Add dev dependencies:
   - `pytest`, `pytest-asyncio` for async test support.
   - `mypy` for static typing.
   - `ruff` (or `flake8`) for linting; choose `ruff` (faster, modern) with a minimal config.
   - `coverage` (or rely on `pytest --cov`) via `pytest-cov`.
4. Configure tool sections / ruff / mypy in `pyproject.toml`.
5. Ensure `src/spearmint/py.typed` exists (already present) to mark typed package.
6. Add initial empty module stubs (only if missing) to match spec future paths without implementation: `branch.py`, `strategies.py`, `logging.py`, `config.py`, `experiment.py`, `registry.py` containing docstring placeholders and TODO markers. Keep them minimal—no logic yet.
7. Create `tests/conftest.py` with shared fixtures (e.g., event loop fixture if needed, in-memory logger fixture stub placeholder).
8. Add a `Makefile` or simple `scripts/` (YAGNI: omit unless necessary). For now supply README section with commands instead of extra tooling.
9. Update `README.md` quickstart section: installation, optional MLflow extra, running tests.
10. Verify installation:
    - `python -m pip install -e .[mlflow]`
    - `pytest -q` (should pass with placeholder tests).

### File-Level Guidance
- `pyproject.toml`: Add dependencies, `[tool.mypy]`, `[tool.ruff]`, and optional extras section.
- `src/spearmint/__init__.py`: Export key public symbols progressively (initially version constant + placeholder). Avoid re-exporting unfinished modules.
- New stub files: Add module-level docstring: purpose + acceptance criteria reference + TODO list.
- `tests/test_imports.py`: Simple smoke test ensuring modules import without error.

### Testing Strategy (TDD Angle)
Write failing smoke tests first (import modules that will be created). Then create stub files to satisfy them.

Test Cases:
1. Import `spearmint` root succeeds.
2. Import each stub module (`from spearmint import branch, strategies, logging, config, experiment, registry`).
3. Access `__version__` attribute from `spearmint`.

Edge Cases Considered:
- Missing optional MLflow: Ensure importing `logging` does not raise if MLflow absent (guarded import placeholder).
- Python versions: Ensure classifiers and requires-python reflect target (e.g., `>=3.9`).

### Acceptance Criteria
- Editable install works.
- Optional MLflow extra declared.
- Lint and type configs present.
- Smoke tests green.
- No unused placeholder logic beyond docstrings.

### Commit Granularity
Recommended commits:
1. Add deps + tool configs.
2. Add stub modules + py.typed confirmation.
3. Add smoke tests + fixtures.
4. README quickstart update.

---

## Detailed Task 2: Core Types & Data Models

Goal: Implement `Branch` and `BranchContainer` plus shared constants/types so later components (strategies, logging) can rely on stable structures. Provide thorough unit tests covering creation, success/failure capture, duration calculation, and serialization basics.

### Subtasks
1. Design `Branch` structure (dataclass or `@dataclass(slots=True)` for perf):
   - Fields: `config_id: str`, `config: dict | BaseModel`, `start_ts: float`, `end_ts: float | None`, `status: Literal['success','failed','skipped']`, `output: Any | None`, `exception_info: ExceptionInfo | None`.
2. Define `ExceptionInfo` lightweight dataclass: `type: str`, `message: str`, `traceback: str`.
3. Computed property: `duration` (float, `end_ts - start_ts` if end available else `None`).
4. Implement factory helpers:
   - `Branch.start(config_id, config)` -> returns Branch with `start_ts=perf_counter()` and default fields.
   - `branch.mark_success(output)` sets `end_ts`, `status`, `output`.
   - `branch.mark_failure(exc)` captures exception info (use `traceback.format_exception`).
   - `branch.mark_skipped(reason)` (store reason inside `exception_info.message` with type `Skip` maybe) — optional for MVP but adds clarity; include TODO if not used yet.
5. Serialization helper: `branch.to_dict(redact: bool = False)` (YAGNI note: keep minimal; include config minus potential secrets—just return raw for MVP with TODO comment on redaction).
6. `BranchContainer` design (simple list wrapper):
   - Class holding `branches: list[Branch]` + iteration support + convenience methods: `successful()`, `failed()`, `by_config_id(id)`.
   - Possibly implement `__iter__`, `__len__`, `__getitem__` to behave like sequence.
7. Status constants / type aliases in `types.py`:
   - `Status = Literal['success','failed','skipped']`
   - Export `STATUSES = {'success','failed','skipped'}`.
8. Add `__all__` exports for public API in module files.
9. Integrate minimal docstrings referencing design spec section numbers.
10. Update `src/spearmint/__init__.py` to export `Branch`, `BranchContainer`.

### File-Level Guidance
- `src/spearmint/branch.py`: Implement dataclasses and helpers.
- `src/spearmint/types.py`: Add literals, Protocol placeholders for future (Strategy, LoggerBackend) as forward refs or simple type aliases; Avoid circular imports.
- `tests/test_branch.py`: New tests.

### Testing Strategy (Write tests first)
Test Cases:
1. `Branch.start` initializes correct defaults (`status` initially maybe 'pending'?). Decide: Use `'pending'` internally or start as `None`; acceptance spec lists only success/failed/skipped. Keep YAGNI: start with `status='success'` only after mark; before that use `'pending'`. Add `PENDING_STATUS` constant internal, not exported.
2. `mark_success` sets `status='success'`, sets `end_ts`, captures output, duration > 0.
3. `mark_failure` sets `status='failed'`, stores exception info type/message/traceback string containing raising function name.
4. `duration` returns None prior to completion.
5. `BranchContainer.successful()` returns only success branches.
6. `by_config_id` returns correct branch or None.
7. Serialization includes expected keys.

Edge Cases:
- Marking success twice raises (protect against misuse) — implement guard raising `RuntimeError`.
- Marking failure after success disallowed similarly.
- Duration extremely small (assert >=0 not >0 to avoid flakiness).
- Exception with Unicode message serialized correctly.

### Implementation Notes
- Use `time.perf_counter()` for timestamps; convert to epoch (optional). Simplicity: store perf_counter floats for duration; add TODO for epoch mapping.
- Provide `finalize(status, output=None, exc=None)` internal method to reduce duplication (DRY) used by `mark_success` / `mark_failure`.
- Keep dependencies minimal: only stdlib. Avoid pydantic dependency here (configs are dict for now).

### Acceptance Criteria
- Branch & BranchContainer implemented with documented public methods.
- All tests green.
- No extraneous dependencies added.
- Clean type checking (mypy no errors for these modules).

### Commit Granularity
1. Add tests (failing) for Branch & BranchContainer.
2. Implement Branch dataclass + helpers until tests pass.
3. Implement BranchContainer + update tests to include container behaviors.
4. Export in `__init__.py`.

### Follow-Up / Deferred
- Redaction logic.
- Extended metrics (retry counts, etc.).
- Config object type normalization (Pydantic model vs dict).

