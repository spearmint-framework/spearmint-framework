# Detailed Task 2: Core Types & Data Models

Goal: Implement `Branch` and `BranchContainer` plus shared constants/types so later components (strategies, logging) can rely on stable structures. Provide thorough unit tests covering creation, success/failure capture, duration calculation, and serialization basics.

## Subtasks
1. Design `Branch` structure (dataclass or `@dataclass(slots=True)` for perf):
   - Fields: `config_id: str`, `config: dict | BaseModel`, `start_ts: float`, `end_ts: float | None`, `status: Literal['pending','success','failed','skipped']`, `output: Any | None`, `exception_info: ExceptionInfo | None`.
2. Define `ExceptionInfo` lightweight type (dict or dataclass): `type: str`, `message: str`, `traceback: str` (keep dict for now—YAGNI vs formal dataclass). Provide `ExceptionInfo` type alias.
3. Computed property: `duration` (float, `end_ts - start_ts` if end available else `None`).
4. Implement factory helpers:
   - `Branch.start(config_id, config)` -> returns Branch with `start_ts=perf_counter()`.
   - `branch.mark_success(output)` sets `end_ts`, `status`, `output`.
   - `branch.mark_failure(exc)` captures exception info (use `traceback.format_exception`).
   - `branch.mark_skipped(reason)` sets status skipped with reason wrapped in `exception_info`.
5. Serialization helper: `branch.to_dict(redact: bool = False)` (return raw for MVP; TODO for redaction).
6. `BranchContainer` design (simple list wrapper):
   - Holds `branches: list[Branch]` + iteration support + convenience methods: `successful()`, `failed()`, `by_config_id(id)`.
7. Status constants / type aliases in `types.py`:
   - `Status = Literal['pending','success','failed','skipped']`
   - `FINAL_STATUSES = {'success','failed','skipped'}`.
8. Add `__all__` exports for public API.
9. Update `src/spearmint/__init__.py` to export `Branch`, `BranchContainer`.

## File-Level Guidance
- `src/spearmint/branch.py`: Implement dataclass and helpers.
- `src/spearmint/types.py`: Add literals and type aliases; avoid circular imports.
- `tests/test_branch.py`: New tests for branch lifecycle + container filters.

## Testing Strategy (TDD)
Write tests first for lifecycle, exceptions, container filters, serialization.

Test Cases:
1. `Branch.start` initializes with `status='pending'` and no end_ts.
2. `mark_success` sets `status='success'`, sets `end_ts`, captures output, duration >= 0.
3. `mark_failure` sets `status='failed'`, stores exception info with type/message/traceback containing raising function name.
4. `duration` returns None prior to completion.
5. `BranchContainer.successful()` returns only success branches.
6. `by_config_id` returns correct branch or None.
7. Serialization includes expected keys and duration value matching computed property.
8. Double finalization raises `RuntimeError`.

Edge Cases:
- Unicode exception messages serialized correctly.
- Very fast execution still yields non-negative duration.
- Skipped branch uses `exception_info.type == 'Skipped'`.

## Implementation Notes
- Use `time.perf_counter()` for timestamps; simple floats are fine.
- Internal `_finalize` helper to DRY success/failure/skip logic.
- Keep dependencies minimal (stdlib only). Config remains dict for now.

## Acceptance Criteria
- Branch & BranchContainer implemented with documented public methods.
- All tests green.
- Clean type checking (mypy no errors for these modules).

## Commit Granularity
1. Add tests (failing) for Branch & BranchContainer.
2. Implement Branch dataclass + helpers until tests pass.
3. Implement BranchContainer + update tests to include container behaviors.
4. Export in `__init__.py`.

## Deferred / TODO
- Redaction logic.
- Extended metrics (retry counts, retries, etc.).
- Config object normalization (Potential pydantic integration later).
