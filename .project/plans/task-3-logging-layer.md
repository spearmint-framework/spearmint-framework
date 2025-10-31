# Task 3: Logging Layer Implementation Plan

Goal: Provide a minimal, pluggable async logging layer with an MLflow backend (optional dependency) and an in-memory test double. It must record Branch lifecycle data (params, status timestamps, exceptions) without coupling business logic to MLflow internals. Ensure graceful degradation if MLflow is not installed.

Guiding Principles: DRY, YAGNI (only what spec & tests need), TDD-first (write tests before implementation), clear error messages, optional dependency isolation, minimal public surface.

## Outcomes / Acceptance Criteria
- `LoggerBackend` Protocol defined (`logging.py`).
- MLflow backend class `MLflowLogger` implementing protocol; skips if mlflow missing with clear message and uses a NoOp fallback unless explicitly requested.
- In-memory backend `InMemoryLogger` for unit tests with query capabilities (store runs in dict).
- Branch execution paths call logger methods in correct order.
- Exceptions logged with type, message, formatted traceback string.
- All methods are async (use `anyio` or `asyncio.to_thread` for MLflow sync calls) while maintaining test determinism.
- Coverage includes success case, failure case, mlflow-missing fallback.

## File Touch Points
- `src/spearmint/logging.py`: Define protocol, implementations, helper utilities.
- `src/spearmint/branch.py`: (May already exist) Ensure Branch fields align; add helper to serialize params if needed.
- `tests/test_logging.py`: New tests for backends & protocol behavior.
- `pyproject.toml`: Add optional dependency group `[project.optional-dependencies]` for mlflow (e.g., `mlflow = ["mlflow>=2.9"]`). Add dev dependency for `anyio` if needed (or avoid by using pure asyncio threads).
- `README.md`: Brief section describing optional MLflow installation.

## Detailed Steps

### 1. Protocol Definition (TDD)
Write test: `test_logging_protocol_exists` verifying attributes of `LoggerBackend` via `typing.Protocol` and `inspect.getmembers`.
Add protocol:
```python
class LoggerBackend(Protocol):
    async def start_run(self, config: dict) -> str: ...
    async def log_params(self, run_id: str, params: dict) -> None: ...
    async def log_status(self, run_id: str, status: str, start_ts: float, end_ts: float, retry_count: int = 0) -> None: ...
    async def log_exception(self, run_id: str, exc_type: str, exc_msg: str, traceback_str: str) -> None: ...
```

### 2. InMemoryLogger Implementation
Tests first:
- `test_inmemory_logger_records_success_run`
  - Start run with sample config, log params, log status; assert stored dict has expected keys and duration calculation validated externally.
- `test_inmemory_logger_records_exception`
  - Simulate exception and log; assert exception fields.
Implementation details:
- Maintain `self._runs: dict[str, dict]`.
- Generate `run_id` via `uuid.uuid4().hex`.
- Provide helper `get_run(run_id)` and `list_runs()` (not part of protocol; internal/testing only). Keep them minimal.

### 3. MLflowLogger Implementation (Optional Dependency)
Tests:
- Use `pytest.importorskip("mlflow")` for tests that require MLflow. If not installed, ensure fallback tests still pass.
- `test_mlflow_logger_start_run_and_status` (skipped if mlflow missing):
  - Patch mlflow functions using monkeypatch to avoid real network / artifact writes.
- `test_mlflow_missing_uses_noop`
  - Force import error via monkeypatch if necessary; instantiate wrapper expecting `NoOpLogger` behavior.
Implementation:
- Attempt import at top inside try/except; set `_MLFLOW_AVAILABLE` flag.
- `MLflowLogger.__init__(self, experiment_name: str | None = None)` sets experiment if available (handle absence gracefully).
- Each protocol method wraps synchronous mlflow calls using `asyncio.to_thread` for non-blocking behavior.
- `log_exception` writes traceback to temporary file (NamedTemporaryFile) then logs as artifact; or simpler: set tag with truncated traceback (YAGNI choose simplest acceptable: tag field `"traceback"`).
- Fallback: If mlflow not available, either raise on use or degrade. MVP spec wants graceful fallback: export `get_logger("mlflow")` that returns `MLflowLogger` or `NoOpLogger`.

### 4. NoOpLogger (Internal)
Single implementation used when mlflow absent; methods do nothing but return a synthetic run_id for `start_run`.
Test: `test_noop_logger_behaves` ensures no exceptions and run_id uniqueness.

### 5. Integration Hooks
Strategy execution code (Task 4) will call:
1. `run_id = await logger.start_run(config)` before Branch execution.
2. `await logger.log_params(run_id, config)` post-start pre-execution.
3. On success: `await logger.log_status(run_id, "success", start_ts, end_ts)`.
4. On exception: `await logger.log_exception(...); await logger.log_status(run_id, "failed", start_ts, end_ts)`.
Write integration tests later in Task 4 referencing InMemoryLogger for determinism.

### 6. Branch Serialization Alignment
Confirm Branch in `branch.py` has fields `config`, `config_id`, `status`, `start_ts`, `end_ts`, `output`, `exception_info`. Add method `to_logging_params()` returning config dict (maybe identity for MVP). Test not needed yet (covered indirectly).

### 7. Dependency & Packaging Updates
Update `pyproject.toml`:
- Add optional dependency group `[project.optional-dependencies]` with key `mlflow = ["mlflow>=2.9"]`.
- Ensure dev group has `pytest`, `mypy`, `ruff` (if not already).
Add extras mention in README.
Test: Not required for packaging but run `pip install -e .[mlflow]` manual instructions in README.

### 8. Documentation
README section "Logging" describing how to install MLflow extra and fallback behavior; short code snippet.

### 9. Edge Cases & Error Handling
- MLflow available but start_run fails: catch exception and raise custom `LoggerError` (define in file) or fallback? MVP: raise.
- Large traceback: store entire string (let MLflow handle size). YAGNI for truncation.
- Concurrent start_run calls: safe (uuid ensures uniqueness). MLflow's internal concurrency okay for single process.

### 10. Testing Strategy Summary
Use pure async tests with `pytest.mark.asyncio`. Avoid real mlflow network; monkeypatch functions (`mlflow.start_run`, `mlflow.log_params`).
Focus: protocol compliance, storage semantics, fallback path.

### 11. Commit Granularity
Recommended commit sequence:
1. Add protocol & InMemoryLogger + tests.
2. Add NoOpLogger + tests.
3. Add MLflow optional import + MLflowLogger stub & tests (skip if missing).
4. Add pyproject optional deps + README docs.
5. Adjust Branch (if needed) + minor tests.

### 12. Future Hooks (Deferred)
Out of scope: metrics, structured artifacts, retry counts beyond parameter presence.

## Checklist Before Marking Complete
- [ ] Tests for protocol, InMemoryLogger, NoOpLogger, MLflowLogger (conditional) created and passing.
- [ ] pyproject updated with optional dependency.
- [ ] README updated.
- [ ] All new public names exported via `__all__` in `logging.py`.
- [ ] mypy passes for new module.
