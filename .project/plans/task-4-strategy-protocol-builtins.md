# Task 4: Strategy Protocol & Built-in Strategies Implementation Plan

Goal: Define the core `Strategy` protocol and implement three built-in strategies (`RoundRobinStrategy`, `ShadowStrategy`, `MultiBranchStrategy`) coordinating Branch creation, async execution patterns, and logging integration. Provide registration API and experiment decorator interface. Ensure deterministic, well-tested behavior for concurrency and return shapes.

Guiding Principles: TDD-first, minimal public API, clear separation (strategy vs logging vs branch lifecycle), robust under async failure modes, DRY across strategies using shared helpers.

## Outcomes / Acceptance Criteria
- `Strategy` Protocol in `strategies.py` with `async def run(self, func, configs, *args, **kwargs)` signature.
- `RoundRobinStrategy` returns direct result of selected single config execution.
- `ShadowStrategy` returns primary config result immediately while scheduling shadow runs for others (background tasks).
- `MultiBranchStrategy` concurrently executes all configs and returns a `BranchContainer` containing `Branch` objects.
- Branch objects created for every executed config (including shadow runs) with accurate timing and status.
- Logging integration calls backend consistently for every Branch.
- Strategy selection deterministic for RoundRobin (rotating index) and primary config selection for Shadow.
- Registration mechanism: `register_strategy(name, strategy_factory)` and `get_strategy(name)`.
- `@experiment` decorator allowing `@experiment(strategy=RoundRobinStrategy(...))` style usage; wraps an async function, injecting orchestration. Returns appropriate shape per strategy.
- Tests covering all execution paths, success/failure, background completion, logging calls ordering, registration, and decorator behavior.

## File Touch Points
- `src/spearmint/strategies.py`: Protocol, strategy classes, helper base class (optional), registration functions.
- `src/spearmint/experiment.py`: Decorator implementation using provided strategy instance.
- `src/spearmint/branch.py`: Ensure `Branch` and `BranchContainer` support needed operations (append, iteration). Possibly add `__iter__` and `add(branch)`.
- `src/spearmint/logging.py`: Already planned in Task 3; integrate by injecting logger instance into strategies or passing through experiment decorator.
- `tests/`: New test modules: `test_strategy_round_robin.py`, `test_strategy_shadow.py`, `test_strategy_multi_branch.py`, `test_strategy_registration.py`, `test_experiment_decorator.py`.

## Detailed Steps

### 1. Define Strategy Protocol (TDD)
Test: `test_strategy_protocol_signature` verifying attributes using `inspect.signature`.
Implementation in `strategies.py`:
```python
class Strategy(Protocol):
    async def run(self, func: Callable[..., Awaitable[Any]], configs: Sequence[dict], *args, logger: LoggerBackend | None = None, **kwargs) -> Any: ...
```
Note: Accept `logger` keyword for injection; default uses NoOp if None.

### 2. Shared Helpers
Implement internal async helper `async def execute_branch(func, config, logger) -> Branch` performing:
- start_ts
- start_run/log_params
- await func(..., config=config) (function should accept config or we adapt signature via decorator)
- set Branch output or exception
- log status/exception
Return Branch.
Test via unit test using InMemoryLogger; `test_execute_branch_success` and `test_execute_branch_failure`.

### 3. BranchContainer
If not present, implement in `branch.py`:
```python
@dataclass
class BranchContainer(Sequence[Branch]):
    branches: list[Branch]
    def __iter__(self): return iter(self.branches)
    def __len__(self): return len(self.branches)
    def __getitem__(self, idx): return self.branches[idx]
    def add(self, branch: Branch): self.branches.append(branch)
```
Test: `test_branch_container_basic_ops`.

### 4. RoundRobinStrategy
Behavior:
- Maintains internal index state (use itertools.cycle or manual modulo).
- On each `run`, selects config at current index, increments index.
- Calls `execute_branch` for chosen config; returns `branch.output` directly (not Branch).
- Provide method `last_branch()` for introspection (non-MVP but useful test; optional). YAGNI: keep minimal.
Tests:
- `test_round_robin_cycles_configs` (call run 3+ times ensure cycling).
- `test_round_robin_failure_propagates` (exception in func surfaces to caller; Branch recorded failed).
- `test_round_robin_logs_branch` uses InMemoryLogger to verify single run logged.
Edge: Empty configs -> raise `ValueError` early.

### 5. ShadowStrategy
Behavior:
- Identify primary config (first or by key `primary_config_id` argument). Others are shadow.
- Execute primary config foreground via `execute_branch`.
- Schedule shadow configs concurrently using `asyncio.create_task` calling `execute_branch`.
- Collect tasks in internal list to allow inspection; no awaited completion before returning.
- Return primary branch output.
- Provide `async def gather_shadows()` for explicit awaiting (test helper).
Tests:
- `test_shadow_strategy_returns_primary_immediately` measure elapsed time difference between primary quick return and slower shadow tasks.
- `test_shadow_strategy_shadow_failures_dont_affect_primary` ensure exceptions caught and logged but not raised.
- `test_shadow_strategy_logging_all_branches` confirm one run_id per config.
Edge: Single config list => behaves like RoundRobin (no shadows) but still returns output.

### 6. MultiBranchStrategy
Behavior:
- Fan-out all configs concurrently; create tasks for each `execute_branch`.
- Await `asyncio.gather(*tasks, return_exceptions=True)`; transform results into BranchContainer.
- If a task raised exception, `execute_branch` should already convert to failed Branch; gather should not raise (since execute_branch catches internally), so ensure `execute_branch` never re-raises.
- Return BranchContainer.
Tests:
- `test_multi_branch_all_success` verifying container length matches config count and statuses.
- `test_multi_branch_mixed_failures` intentionally fail subset; confirm statuses and exception info.
- `test_multi_branch_logging_per_branch` verifying logger run count.
Edge: Empty configs -> return empty BranchContainer or raise? Decide: raise `ValueError` for consistency.

### 7. Registration API
In `registry.py` (existing): Provide functions if not implemented:
```python
_STRATEGIES: dict[str, Callable[[], Strategy]] = {}

def register_strategy(name: str, factory: Callable[[], Strategy]):
    if name in _STRATEGIES: raise ValueError(f"Strategy '{name}' already registered")
    _STRATEGIES[name] = factory

def get_strategy(name: str) -> Strategy:
    try: return _STRATEGIES[name]()
    except KeyError: raise ValueError(f"Unknown strategy '{name}'")
```
Tests: `test_strategy_registration_and_lookup`.

### 8. Experiment Decorator
`experiment.py`:
Interface:
```python
def experiment(strategy: Strategy):
    def wrapper(func):
        @functools.wraps(func)
        async def inner(*args, **kwargs):
            configs = kwargs.pop("configs", None)
            if configs is None:
                raise ValueError("'configs' argument required for experiment execution")
            logger = kwargs.pop("logger", None)
            return await strategy.run(func, configs, *args, logger=logger, **kwargs)
        return inner
    return wrapper
```
Tests:
- `test_experiment_decorator_round_robin`
- `test_experiment_decorator_shadow`
- `test_experiment_decorator_multi_branch`
- `test_experiment_requires_configs`
Edge: Allow passing configs as positional maybe? YAGNI: enforce keyword.

### 9. Logging Integration Validation
Use InMemoryLogger instance in strategy tests; assert number of runs equals number of executed configs.
Shadow-specific: Wait for `gather_shadows` then assert all logs present.

### 10. Concurrency Safety & Cancellation (Minimal)
Ensure created tasks stored so user can cancel if needed; document in code comment. Tests do not cover cancellation for MVP.

### 11. Type Checking & Mypy
Add precise return types:
- RoundRobinStrategy.run -> `Any`
- ShadowStrategy.run -> `Any`
- MultiBranchStrategy.run -> `BranchContainer`
Consider generics? MVP skip generics (YAGNI).
Add `__all__` exports.

### 12. Test Utilities
Add fixture in `tests/conftest.py` for sample configs list and `InMemoryLogger` instance.
Add simple async test function fixture `async def sample_func(x: int, config: dict) -> int` returning `x + config.get("delta", 0)`; failure case controlled via config flag.

### 13. Commit Sequence
1. Protocol + execute_branch helper + tests.
2. BranchContainer adjustments + tests.
3. RoundRobinStrategy + tests.
4. ShadowStrategy + tests.
5. MultiBranchStrategy + tests.
6. Registration API + tests (if not already present / extend).
7. Experiment decorator + tests.
8. Final integration test with mixed strategies and logger.

### 14. Edge Cases
- Empty configs -> ValueError.
- Non-async target function: Decorator can detect and wrap with `asyncio.to_thread` (optional). MVP: enforce async only; raise TypeError if `not asyncio.iscoroutinefunction(func)`. Test this.
- Config mutation by user after pass-in: Accept; no defensive copy (document). YAGNI.

### 15. Documentation
Update README: usage examples for each strategy and decorator.

### 16. Future Deferred
Streaming container; cancellation; semaphore limiting; strategy composition.

## Checklist Before Marking Complete
- [ ] Protocol + helper implemented and tested.
- [ ] All three strategies implemented with passing tests.
- [ ] Registration API verified.
- [ ] Decorator implemented and tested across strategies.
- [ ] Logging integrated with InMemoryLogger in tests.
- [ ] README updated with examples.
- [ ] mypy passes for new code.
